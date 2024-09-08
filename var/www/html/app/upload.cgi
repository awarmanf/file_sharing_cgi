#!/usr/bin/perl -w

#
# File Sharing Web Application
#
# upload.cgi
#

use strict;
use CGI;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use Time::Local;
use lib '.';
use My::Session;
use My::TimeConvert;

# meski pakai taint mode tidak ngaruh sama sekali
# Set PATH and remove some environment variables for running in taint mode.
#$ENV{'PATH'} = '/bin:/usr/bin:/usr/local/bin';
$ENV{'PATH'} = '';
delete @ENV{ 'IFS', 'CDPATH', 'ENV', 'BASH_ENV' };


$CGI::DISABLE_UPLOADS   = 0;
$CGI::POST_MAX = MAXFILESIZE*1024*1024; # this MAXFILESIZE on ../html/js/functions.js too

# session validation
&cekSession;

my $cgi = new CGI;

my $postmax = sprintf ("%d",$CGI::POST_MAX/1024/1024); 
my $quotamax = sprintf ("%d",$userQuota/1024/1024);
my ($filename,$filedesc,$fileLM,$fileLMD,$fileEpoch,$mysqlTime,$userq);

if ( $ENV{REQUEST_METHOD} eq 'POST' ) {
  $filename = $cgi->param("filename");
  $filedesc = $cgi->param("filedesc");
  $fileLM = $cgi->param("lastModified");
  $fileLMD = $cgi->param("lastModifiedDate");

} else {

  $userq = sprintf("%.2f",$quotaUsage/1024/1024); 

  if ($quotaUsage >= $userQuota) {

    printHeader($cgi, "File Sharing Web Application");

    print <<BODY_HTML2;
<b id="welcome">Hi, <i>$username</i>,</b>
<p style="text-align:center;color:red;">Your quota has been exceeded. You can't upload any file.<br />
Delete your file(s) to save the quota.<br/>
You need to reload this page after deleting some files.</p>
<p>&nbsp;</p>
BODY_HTML2

    printFooter('y');
    print $cgi->end_html;
    exit;
  }

  printHeader($cgi, "File Sharing Web Application");

  print <<BODY_HTML2;
Welcome <b id="welcome">$username</b>,
<form name="myForm" action="/app/upload.cgi" method="post" enctype="multipart/form-data" accept-charset="utf-8" onsubmit="return validateForm()">
<p>Choose file to upload (maximum file size is $postmax MB): 
<p><input type="file" id="fileinput" name="filename" />
<p>Enter description for this file (80 chars maximum):
<br /><input type="text" id="filedesc" name="filedesc" maxlength="80" style="width:97%;font-size:.9em" placeholder="Input the file description here.">
<p><input type="hidden" id="fileLM" name="lastModified"></p>
<p><input type="hidden" id="fileLMD" name="lastModifiedDate"></p>
<p align="right"><input type="reset" name="Reset">&nbsp;<input id="submit2" type="submit" name="Submit" value="Upload File" />
</form>
<p>&nbsp;</p>
BODY_HTML2

  printFooter('n');
  print $cgi->end_html;
  exit;
}

my $safe_filename_characters = "a-zA-Z0-9_.-";
my $upload_dir = UPLOADDIR."/$userid";

if ( !$filename )
{
  print $cgi->header();
  print "There was a problem uploading your file (try a smaller file).";
  exit;
}

# remove trailing '/' or '\'
if ( $filename =~ /.*(\\|\/)(.*)/ ) {  
  $filename=$2 if ($2);  
}
$filename =~ tr/ /_/;
$filename =~ s/[^$safe_filename_characters]//g;
if ( $filename =~ /^([$safe_filename_characters]+)$/ )
{
  $filename = $1;
} else {
  die "Filename contains invalid characters";
}

my $upload_filehandle = $cgi->upload("filename");

# create subdirectory if not exist
mkdir ($upload_dir) if (! (-e $upload_dir));
open ( UPLOADFILE, ">$upload_dir/$filename" ) or die "$!";
binmode UPLOADFILE;

while ( <$upload_filehandle> )
{
  print UPLOADFILE;
}

close UPLOADFILE;

my $filesize = (stat("$upload_dir/$filename"))[7];

if ($fileLM) {
  # dibagi 1000
  $fileLM = $fileLM/1000;
  ($fileEpoch,$mysqlTime) = epoch2datetime($fileLM);
  utime($fileEpoch,$fileEpoch, "$upload_dir/$filename");
}

my $upload_date = &saveUpload($filename,$filedesc,$filesize,$mysqlTime);
my $datelimit = &datetime2epoch($upload_date) + UPTIME*24*3600;
my $htmlline = "";
$datelimit = &epoch2datetime($datelimit); 
if (UPTIME > 0) {
 $htmlline = "It is valid until <mark>$datelimit</mark> before automatically deleted.";
} else {

}

$userq = sprintf("%.2f",$quotaUsage/1024/1024); 

printHeader($cgi, "File Sharing Web Application");

$filesize = &formatNumber($filesize);
print <<BODY_HTML2;
<br />Upload successful !<br /><em>
<br />Name: $filename ($filesize KB)
<br />Last Modified: $mysqlTime</em>
<br />
<p>The link of your file</p>
<p><i>http://$ENV{'SERVER_NAME'}/app/get.cgi?id=$userid&f=$filename</i></p>
<p>$htmlline</p>
<p>&nbsp;</p>
BODY_HTML2

printFooter('y');
print $cgi->end_html;

#
# Subs
#

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


  print <<BODY_HTML;
<div id="main">
<div id="profile">
<img src="images/logo-blue.png" alt="Your Company">
<p style="text-align:right;font-family:sans-serif;font-size:.8em;"><b>Quota $userq MB of $quotamax MB</b></p>
<p>&nbsp;</p>
BODY_HTML
}

sub printFooter {

  my ($upload) = @_ ;

  if ($upload eq 'y') {
    print <<FOOTER;
<p>&nbsp;</p>
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

  } else {

    print <<FOOTER;
<p>&nbsp;</p>
<table style="width:100%;">
<tr>
  <td style="width:25%;text-align:center;"><a href="JavaScript:newPopup('/app/files.cgi');" id="id01">My File</a></td>
  <td style="width:25%;text-align:center;">Upload File</td>
  <td style="width:25%;text-align:center;"><a href="sendnotif.cgi" id="id01">Send Email</a></td>
  <td style="width:25%;text-align:center;"><a href="logout.cgi" id="id01">Logout</a></td>
</tr>
</table>
</div>
</div>
FOOTER
  }
}

