#!/usr/bin/perl -wT

#
# File Sharing Web Application
#
# sendnotif.cgi
#

use strict;
use CGI;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use POSIX qw(strftime);
use Time::Local;
use lib '.';
use My::Session;
use My::TimeConvert;

$CGI::DISABLE_UPLOADS   = 0;
$CGI::POST_MAX          = 1024;

# session validation
&cekSession;

my $cgi = new CGI;
my $quotamax = sprintf ("%d",$userQuota/1024/1024);
my $userq = sprintf("%.2f",$quotaUsage/1024/1024); 
my $filenames = &sendNotif;

if ( $ENV{REQUEST_METHOD} eq 'POST' ) {

  &sendmail($filenames);

  checkSendmail ('File Sharing Web Application', 'Thanks for your notification', 'The process upload is completed. A notification has been sent to recipient(s) which contains path to download the file(s).');

} else {

  printHeader($cgi, "File Sharing Web Application");

if ($filenames eq 'null') {
  print <<BODY_HTML_0;
<div id="main">
<div id="profile">
<img src="images/logo-blue.png" alt="Your Company">
<center>
<p>&nbsp;</p>
<p>You must select file(s) or upload a file before using this module.</p>
<p>&nbsp;</p>
<p><a href="upload.cgi" id="id01">Back</a></a>
</center>
</div>
</div>
BODY_HTML_0
  print $cgi->end_html;
  exit(1);
}

  print <<BODY_HTML_1;
<div id="main">
<div id="profile">
<img src="images/logo-blue.png" alt="Your Company">
<p align="center"><b>Send Email Notification to Your Friend(s)</b></p>
<table>
<tr valign="top">
  <td colspan="3">
  <form name="myForm" method="post" action="" onsubmit="return validateNotif()">
  </td>
</tr>
<tr>
  <td rowspan="2" style="width: 40%;">
BODY_HTML_1

  my (@emailAll, @emailList, $email);
  
  open (FI,"<${\EMAILALL}") or die "Can not open ${\EMAILALL}\n";
  while (<FI>) {
    chomp;
    push (@emailAll,$_);
  }
  close (FI);
  @emailAll = sort(@emailAll);

  open (FI,"<${\EMAILLIST}") or die "Can not open ${\EMAILLIST}\n";
  while (<FI>) {
    chomp;
    push (@emailList,$_);
  }
  
  print "<select name=\"emails\"  size=\"15\" multiple=\"multiple\" style=\"width:215px\" id=\"s\">\n";
  foreach $email (@emailAll) {
    if (grep(/^$email$/,@emailList)) {
      print "<option style=\"font-weight: bold\" value=\"$email\">$email</option>\n";
    } else {
      print "<option value=\"$email\">$email</option>\n";
    }
  }
  print "</select>\n";

  print <<BODY_HTML_21;
  </td>
  <td align="center" style="width: 20%;">
    <input type="button" value="&gt;&gt;" onclick="listbox_moveacross('s', 'd1')" /><br />
    <input type="button" value="&lt;&lt;" onclick="listbox_moveacross('d1', 's')" /> 
  </td>
  <td style="width: 40%;">
    To:<br/>
    <select name="valTo" id="d1" size="5" multiple style='width:215px;'>
    </select>
    <input type="hidden" name="valBcc" value="$username">
  </td>
</tr>
<tr>
  <td align="center">
    <input type="button" value="&gt;&gt;" onclick="listbox_moveacross('s', 'd2')" /><br/>
    <input type="button" value="&lt;&lt;" onclick="listbox_moveacross('d2', 's')" />   
  </td>
  <td>
    Cc:<br/>
    <select name="valCc" id="d2" size="5" multiple style='width:215px;'>
    </select>
  </td>
</tr>
<tr>
   <td colspan="3">Body:<br/>
<textarea name="body" id="body" maxlength="600" style="width:566px;height:100px;font-family:Arial,Helvetica,sans-serif;font-size:13px;" placeholder="Write your message here.">
</textarea>
Footer:<br/>
<div style="width:566px;font-family:Arial,Helvetica,sans-serif;font-size:14px;background-color:#FFFFFF;border:1px solid black;">
BODY_HTML_21

my @filearr = split("\x8f",$filenames);
my ($fileName, $fileDesc, $fileNameDesc);

##foreach $fileNameDesc (@filearr) {
##  ($fileName,$fileDesc) = split("\x8d",$fileNameDesc);
##  print "$fileName ($fileDesc)\n";
##  print "Link: http://$ENV{'SERVER_NAME'}/app/get.cgi?id=$userid&f=$fileName\n";
##}

foreach $fileNameDesc (@filearr) {
  ($fileName,$fileDesc) = split("\x8d",$fileNameDesc);
  print "<p>Link download for <em>$fileDesc</em> here:</p>";
  print "<p><a href=\"http://$ENV{'SERVER_NAME'}/app/get.cgi?id=$userid&f=$fileName\">$fileName</a><br></p></div>";
}

  print <<BODY_HTML_22;
<p style="text-align:right;font-family:sans-serif,monospace;font-size:12px">You will get email notification automatically.</p>
   </td>
</tr>
<tr>
  <td align="center" colspan="3">
    <input type="submit" name="Submit" value="Submit">
    </form>
  </td>
</tr>
<tr>
  <td align="right" colspan="3"><a href="upload.cgi" id="id01">Back</a></td>
</tr>
</table>
</div>
</div>
BODY_HTML_22

  print $cgi->end_html;

}

sub sendmail {
  use Net::SMTP;
 
  my ($filenames) = @_;
  my $timeout = 60;
  # set msgid
  my $random = rand;
  my @arr    = split(/\./,$random);
  my $msgid  = '<'.$arr[1].'@localhost.localdomain>';
  my $bcc    = BCC."\@".DOMAIN;
  my ($value, $sender, @rcpTos, @rcpCcs, @rcpAll, $body);
  
  foreach $value ( $cgi->param('valTo') ) {
    $value = $value.'@'.DOMAIN;
    push (@rcpTos, $value);
  }
  push (@rcpAll, @rcpTos);

  foreach $value ( $cgi->param('valCc') ) {
    $value = $value.'@'.DOMAIN;
    push (@rcpCcs, $value);
    # because in Net::SMTP there is no smtp->cc function
    push (@rcpAll, $value);
  }

  foreach $value ( $cgi->param('valBcc') ) {
    $sender=$value.'@'.DOMAIN;
  }
  
  $body = $cgi->param('body');

  # open connection
  my $smtp = Net::SMTP->new(MAILSERVER, Timeout => $timeout, debug => 1,)
      or die "Can not connect to MAILSERVER\n";
  
  # smtp authentication
  $smtp->auth($username,$password);
  if ( ! $smtp->ok ) {

     print CGI::header(-type=>"text/html"),
        CGI::start_html,
        CGI::h1($smtp->code(),": ",$smtp->message()),
        CGI::end_html;
    exit(1);
  }

  $smtp->mail($sender);
  foreach $value (@rcpAll) { 
    $smtp->to($value);

    # check if recipient valid
    if ( ! $smtp->ok ) {
      checkSendmail ( 'Send Notification is Failed', 'Your notification is failed', "You can't send notification to the email address: $value</p><p>".$smtp->message());
      exit(1);
    }
  }

  # sent to sender itself
  $smtp->to($sender);
  $smtp->to($bcc);
  $smtp->data();
  $smtp->datasend("Message-ID: $msgid\n");
  $smtp->datasend("From: $sender\n");
  $value = join (",", split (/ /,"@rcpTos"));
  $smtp->datasend("To: $value\n");
  if (@rcpCcs) {
    $value = join (",", split (/ /,"@rcpCcs"));
    $smtp->datasend("Cc: $value\n");
  }
  $smtp->datasend("Subject: File(s) has been uploaded by $sender\n");
  $smtp->datasend("Content-Type: text/html; charset=UTF-8");
  $smtp->datasend("Content-Transfer-Encoding: 7bit");
  $smtp->datasend();

  $smtp->datasend("<!DOCTYPE html><html><head><meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\"></head><body><p><br></p><p><pre>$body</pre></p>");
    
  my @filearr = split("\x8f",$filenames);
  my ($fileName, $fileDesc, $fileNameDesc);
  foreach $fileNameDesc (@filearr) {
    ($fileName,$fileDesc) = split("\x8d",$fileNameDesc);
    $smtp->datasend("<p>Link download for <em>$fileDesc</em> here:</p>");
    $smtp->datasend("<p><a href=\"http://$ENV{'SERVER_NAME'}/app/get.cgi?id=$userid&f=$fileName\">$fileName</a><br>");
  }
  $smtp->datasend("</p><p>---<br></p><p>Thank You,<br></p>");
  $smtp->datasend("<p>Sent by: <a href=\"http://$ENV{'SERVER_NAME'}/app\">File Sharing Application</a></p><p><br></p></body></html>");
  $smtp->dataend;
  $smtp->quit;
}


sub checkSendmail {

  my ($title, $status, $message) = @_;

  printHeader($cgi, $title);

  print <<BODY_HTML;
<div id="main">
<div id="profile">
<img src="images/logo-blue.png" alt="Your Company">
<p><p style="text-align:right;font-family:sans-serif,monospace;font-size:12px">Quota $userq MB of $quotamax MB</p>
<p>&nbsp;</p>
<p>$status !</p>
<p>$message</p>
<p>&nbsp;</p>
BODY_HTML

  printFooter('y');
  print $cgi->end_html;

}

sub printHeader {
  my ($cgi, $title) = @_ ;

  print $cgi->header(-type=>"text/html");
  print $cgi->start_html(-title => "$title",
                       -head  => [

             $cgi->Link({'rel'    => 'stylesheet',
                        'type'   => 'text/css',
                        'href'   => 'css/style.css'}),
      
            $cgi->Link({'rel'    => 'stylesheet',
                        'type'   => 'text/css',
                        'href'   => 'font-awesome/css/font-awesome.min.css'}),

            $cgi->Link({'rel'    => 'shortcut icon',
                        'href'   => 'images/logo.ico',
                        'type'   => 'image/x-icon'})],

                        -script  => { -type=>'text/javascript',-src=>'/js/functions.js'},

                        -meta    => {
                           'keywords'      => 'File Sharing Web Application',
                           'copyright'     => 'awarmanf@yahoo.com',
                           'Cache-Control' => 'no-cache',
                           'robots'  => 'index,follow'});

}

sub printFooter {

  my ($upload) = @_ ;

  print <<FOOTER;
<table style="width:100%;">
<tr>
  <td style="width:25%;text-align:center;"><a href="JavaScript:newPopup('/app/files.cgi');" id="id01">My File</a></td>
  <td style="width:25%;text-align:center;"><a href="upload.cgi" id="id01">Upload File</a></td>
  <td style="width:25%;text-align:center;"><a href="sendnotif.cgi" id="id01">Send Email</a></td>
  <td style="width:25%;text-align:center;"><a href="logout.cgi" id="id01">Logout</a></td>
</tr>
</table>
</div>
</div>
FOOTER

}

