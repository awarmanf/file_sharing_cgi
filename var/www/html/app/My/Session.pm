package My::Session;

#
# File Sharing Application
#

use base qw(Exporter);
use POSIX qw(strftime);
use strict;
our @EXPORT = qw(UPLOADDIR EMAILALL EMAILLIST MAXFILESIZE MAILSERVER UPTIME DOMAIN BCC $username $password $userid $quotaUsage $userQuota cekLogin cekSession saveUpload sendNotif myFiles saveDownload delSession formatNumber);
our @EXPORT_OK = qw();

use CGI qw(:standard);
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use CGI::Session ( '-ip_match' );
use DBI;
use Crypt::RC4;

$CGI::DISABLE_UPLOADS  = 0;
$CGI::POST_MAX         = 10240;

# Directory
use constant UPLOADDIR => '/data/upload';
use constant EMAILALL  => '/var/www/html/app/data/emails.all.txt';
use constant EMAILLIST  => '/var/www/html/app/data/emails.list.txt';
use constant SESIDIR   => '/var/www/session';
use constant IDLEXPIRE => 3600; # '+1h' or 3600 seconds
use constant EXPIRE    => '+1d';
use constant LOGOUTEXP => 'Thu, 01-Jan-1970 00:00:00 GMT';
use constant LOGINPAGE => 'index.cgi';
use constant QUOTAMAX  => 262144000; # 250 MB
# Maxiumum file size to upload also edit MAXFILESIZE on ../../html/js/functions.js
use constant MAXFILESIZE => 150; # 150 MB
# Set how many days file will be kept on the server (0 means will be keep forever)
use constant UPTIME => 120;
# Authentication using LDAP
use constant DOMAIN => 'domain.org';
use constant PROTOCOL  => 'LDAP';
use constant MAILSERVER => 'mail.domain.org';
# BCC
use constant BCC => 'admin';
# MySQL
use constant DB => 'webupload';
use constant HOSTDB => 'localhost';
use constant PORTDB => '3306';
use constant USERDB => 'user1';
use constant PASSDB => 'password1';

our ($username, $password, $userid, $quotaUsage, $userQuota);

# Session
my $SID  = 'JCRYPTIONSESSION'; # jcryption's cookie
my $SSID = 'MYSID'; # name of cookie instead of CGISESSID
my $passphrase = 'rumpelstiltskin';

sub authen {
  my ($protocol,$user,$pass) = @_;
  my ($server);

  if ($protocol eq 'LDAP') {
    # LDAP
    use Net::LDAP;
    
    $server = MAILSERVER;
    my $base   = 'ou=people,dc=domain,dc=org';
  
    my $ldap = Net::LDAP->new($server) or return "cannot";
    my $dn   = "uid=$user,$base";
    my $mesg = $ldap->bind($dn, password=>$pass);
    if ($mesg->code) { return "invalid"; }
    return "true";

  } elsif ($protocol eq 'POP') {
    # POP
    use Net::POP3;
  
    $server = MAILSERVER;
  
    my $pop = Net::POP3->new($server) or return "cannot";
    defined ($pop->login($user, $pass)) or return "invalid";
    return "true";

  }
}

sub cekLogin {
  my ($user,$pass) = @_;
  my $result;

  if ( (!$user) || (!$pass) ) {
    &gotoLogin("askinput",$SID);
  } else {
    $result = &authen(PROTOCOL,$user,$pass);
    &gotoLogin($result,$SID) if ($result ne "true" );

    $username = $user;
    $password = RC4($passphrase,$pass);   
    # set cookie name instead of default
    CGI::Session->name($SSID);
    my $session = new CGI::Session("driver:File", undef, {Directory=>SESIDIR});
    $session->param('username', $username);
    $session->param('password', $password);

    # set cookie
    my $cookie1 = CGI::cookie(-name=>$SID,-value=>'',-expires=>LOGOUTEXP);
    my $cookie2 = CGI::cookie(-name=>$SSID,-value=>$session->id,-expires=>EXPIRE);

    # save creation time or ctime to database
    my $dbh = DBI->connect(
            "DBI:mysql:database=${\DB};host=${\HOSTDB};port=${\PORTDB}", USERDB, PASSDB)
              or  &dbdie;

    # cek if username exist and is_locked is TRUE
    my $sth = $dbh->prepare("SELECT id,is_locked,quota 
                      FROM user_db WHERE username=?") 
                or return "Database error.";
    $sth->execute($username);
    
    my ($is_locked,$quota);
    my $login_date = strftime ("%F %T", localtime);
    # save login_date to session
    $session->param('login_date',$login_date);
    
    if (my $rec = $sth->fetchrow_hashref) {
      $userid = $rec->{id};
      $is_locked = $rec->{is_locked};
      $quota = $rec->{quota};
      # save login_date to database
      $sth = $dbh->prepare("UPDATE user_activity 
                     SET last_login='$login_date' WHERE userid=?")
                or &dbdie;
      $sth->execute($userid);
    } else {
      # username not exist so insert into table user_db
      $sth = $dbh->prepare("INSERT INTO user_db (username) VALUES (?)") 
                or &dbdie;
      $sth->execute($username);
      # get id
      $sth = $dbh->prepare("SELECT LAST_INSERT_ID()") 
                or &dbdie;
      $sth->execute();
      $userid = $sth->fetchrow_array;
      # default value for is_locked is 1
      $is_locked = 1;
      # save login_date to database
      $sth = $dbh->prepare("REPLACE INTO user_activity 
                     VALUES ($userid,'$login_date',NULL)") or &dbdie;
      $sth->execute();
      $quota = QUOTAMAX;
    }
    # save quota to session
    $session->param('quota', $quota);
    
    # if locked
    if (!$is_locked) {
      &gotoLogin("blocked",$SID);
    }

    $session->param('userid',$userid);
    print CGI::header(-type=>"text/html",-location=>"upload.cgi",
                      -cookie=>[$cookie1,$cookie2]);
    exit;
  }
}

sub cekSession {
  # cek if session is passed to server
  CGI::Session->name($SSID);
  my $session = CGI::Session->load("driver:File", undef, {Directory=>SESIDIR});

  # expire the session itself after sometime idle
  $session->expire(IDLEXPIRE);

  if($session->is_expired) {
    &gotoLogin("expired",$SSID);
  } elsif($session->is_empty) {
    &gotoLogin("empty",$SSID);
  } else {
    #get username, password & userid
    $username = $session->param('username');
    $password = RC4($passphrase, $session->param('password'));
    $userid = $session->param('userid');
    $userQuota = $session->param('quota');
  }

  my $dbh = DBI->connect(
              "DBI:mysql:database=${\DB};host=${\HOSTDB};port=${\PORTDB}", USERDB, PASSDB)
            or  &dbdie;
  $quotaUsage = &getQuota($dbh,$userid);
}

sub getQuota {
  # get user quota
  my ($dbh,$id) = @_;
  my $sth = $dbh->prepare("SELECT SUM(filesize) FROM user_files 
                    WHERE userid=? AND is_deleted IS FALSE") 
              or &dbdie;
  $sth->execute($id);
  return $sth->fetchrow_array || 0;
}

sub saveUpload {
  my ($filename,$filedesc,$filesize,$fileLM) = @_;
  
  # cek if session is passed to server
  CGI::Session->name($SSID);
  my $session = CGI::Session->load("driver:File", undef, {Directory=>SESIDIR});
  my $upload_date = strftime ("%F %T", localtime);
  my $login_date = $session->param('login_date');
  my $ip_address = $session->param('_SESSION_REMOTE_ADDR');
  $userid = $session->param('userid');

  my $dbh = DBI->connect(
              "DBI:mysql:database=${\DB};host=${\HOSTDB};port=${\PORTDB}", USERDB, PASSDB)
            or  &dbdie;

  # update table upload_history
  my $sth = $dbh->prepare("INSERT INTO upload_history 
               VALUES ($userid,'$upload_date','$filename','$fileLM','$login_date','$ip_address')") 
            or &dbdie;
  $sth->execute();
  
  # update table user_files
  # first check if the filename already exist
  $sth = $dbh->prepare("SELECT filename 
                 FROM user_files 
                 WHERE filename='$filename' AND userid=$userid;")
         or &dbdie;
  $sth->execute();
  $filedesc =~ tr/'/"/;
  if ($sth->fetchrow_array) {
    $sth = $dbh->prepare("UPDATE user_files
                   SET filedesc='$filedesc',filesize=$filesize,lastmodified='$fileLM',is_deleted=0
                   WHERE userid=$userid AND filename='$filename'")
           or &dbdie;
  } else {
    $sth = $dbh->prepare("INSERT INTO user_files
                   VALUES ($userid,'$filename','$filedesc',$filesize,'$fileLM',NULL,0,0)") 
           or &dbdie;
  }
  $sth->execute();

  # update table user_activity
  $sth = $dbh->prepare("UPDATE user_activity
                 SET last_upload='$upload_date'
                 WHERE userid=$userid")
         or &dbdie;
  $sth->execute();

  # get user quota
  $quotaUsage = &getQuota($dbh,$userid);
  # save to session
  $session->param('upload_date',$upload_date);
  $session->param('filename',$filename);
  $session->param('filesize',$filesize);
  $session->param('filedesc',$filedesc);
  # to determine if the file is upload or select
  $session->param('mode','upload');
  
  return $upload_date;
}

sub sendNotif {
  # cek if session is passed to server
  CGI::Session->name($SSID);
  my $session = CGI::Session->load("driver:File", undef, {Directory=>SESIDIR});

  if ( defined ($session->param('mode')) ) {
    if ( $session->param('mode') eq 'upload' ) {
      #return $session->param('filename');
      my $fileNameDesc = join("\x8d",$session->param('filename'),$session->param('filedesc'));
      return $fileNameDesc;
    }
    if ( $session->param('mode') eq 'select' ) {
      return $session->param('filenames');
    } else {
      return 'null';
    }
  } else {
    return 'null';
  }
}

sub saveDownload {
  my ($id, $filename) = @_;
  my $download_date = strftime ("%F %T", localtime);

  my $dbh = DBI->connect(
             "DBI:mysql:database=${\DB};host=${\HOSTDB};port=${\PORTDB}", USERDB, PASSDB)
            or  &dbdie;

  # update download date & num_of_download
  my $sth = $dbh->prepare("SELECT num_of_download
                    FROM user_files
                    WHERE filename='$filename' AND userid=$id") 
            or &dbdie;
  $sth->execute();
  my $num_of_download = $sth->fetchrow_array;
  $num_of_download++;

  $sth = $dbh->prepare("UPDATE user_files
                    SET download_date='$download_date',num_of_download=$num_of_download
                    WHERE filename='$filename' AND userid=$id") 
            or &dbdie;
  $sth->execute();
}

sub myFiles {

  my ($id,$aref,$status) = @_;
  my $upload_dir = UPLOADDIR."/$id";
  my ($fileName, $fileDesc, $fileNameDesc);

  my $dbh = DBI->connect(
              "DBI:mysql:database=${\DB};host=${\HOSTDB};port=${\PORTDB}", USERDB, PASSDB)
            or  &dbdie;
  my $sth;

  if (@$aref gt 0) {

    if ($status eq 'Delete') {
      foreach $fileNameDesc ( @$aref ) {

        CGI::Session->name($SSID);
        my $session = CGI::Session->load("driver:File", undef, {Directory=>SESIDIR});
        ($fileName,$fileDesc) = split ("\x8d",$fileNameDesc);
        # delete file in mysql
        $sth = $dbh->prepare("UPDATE user_files
                     SET is_deleted=TRUE
                     WHERE userid=? AND filename=?") or &dbdie;
        $sth->execute($id,$fileName);

        $session->param('mode','delete');
        # $session->param('filenames',());

        # delete file in subfolder
        unlink ("$upload_dir/$fileName");

        # get user quota
        $quotaUsage = &getQuota($dbh,$id);
      }
    }

    if ($status eq 'Select') {
      CGI::Session->name($SSID);
      my $session = CGI::Session->load("driver:File", undef, {Directory=>SESIDIR});
      $session->param('filenames', join("\x8f",@$aref));
      # to determine if the file is upload or select
      $session->param('mode','select');
    }
  }

  $sth = $dbh->prepare("SELECT filename,filedesc,filesize,lastmodified
                 FROM user_files 
                 WHERE userid=? AND is_deleted=FALSE
                 ORDER BY filesize") or &dbdie;

  $sth->execute($id);
  
  my (@row);
  my $i = 1;

  my $newStyle=<<CSS;
table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
}
th, td {
    padding: 5px;
    font-family: Verdana;
    font-size: 12px;
    color: #000000;
}
th {
    background-color: #FFFFCC;
}
table tr:nth-child(even) {
    background-color: #eee;
}
table tr:nth-child(odd) {
   background-color:#fff;
}
.myfont {
   font-family: Verdana;
   font-size: 12px;
   font-weight: normal;
   color: #000000;
}
a {
  text-decoration:none;
  color: #0000fa;
}
CSS

  my $cgi = new CGI;

  print $cgi->header();

  print $cgi->start_html(-title => "File Sharing Web Application",
                       -head  => [
            $cgi->Link({'rel'    => 'shortcut icon',
                        'href'   => '/images/logo.ico',
                        'type'   => 'image/x-icon'})],

                        -script  => { -type=>'text/javascript',-src=>'/js/functions.js'},
                        -style   => { -code=>$newStyle},
                        -meta    => {
                           'keywords'      => 'File Sharing Web Application',
                           'copyright'     => 'awarmanf@yahoo.com',
                           'Cache-Control' => 'no-cache',
                           'robots'  => 'index,follow'});

  print <<TBL_1;
<form name="form1" action="" method="post" onSubmit="return SureConfirm()">
<table border=1>
<tr>
  <th>No.</th>
  <th>Name</th>
  <th>Size (KB)</th>
  <th>Last Modified</th>
  <th><img src="/images/edit_action.gif"></th>
</tr>
TBL_1

  while (@row = $sth->fetchrow_array) {
    my $filesize = formatNumber($row[2]);
    print <<TBL_2;
<tr>
  <td align="right">$i</td>
  <td><a href="http://$ENV{'SERVER_NAME'}/app/get.cgi?id=$id&f=$row[0]" title="$row[1]">$row[0]</td>
  <td align="right">$filesize</td>
  <td>$row[3]</td>
TBL_2

    if ( ($status eq 'Select') and (grep(/$row[0]/,@$aref)) ) {
        print "<td><input type=\"checkbox\" name=\"name\" value=\"$row[0]\x8d$row[1]\" checked=\"yes\"></td></tr>\n";
    } else {  
        print "<td><input type=\"checkbox\" name=\"name\" value=\"$row[0]\x8d$row[1]\"></td></tr>\n";
    }
    $i++;
  }

  print "<tr><td colspan=\"5\" style=\"text-align:right;background-color:#FFFFCC;border:0px;\">\n";
  if ($status eq 'Select') {
    print "<input class=\"myfont\" type=\"submit\" name=\"Select\" value=\"Send Selection\">\n";
    print "<p align='center'>Close this popup and click the <i>Send Email</i>.\n";
  } else {
    print "<input class=\"myfont\" type=\"submit\" name=\"Delete\" value=\"Delete Selection\">\n";
    print "<input class=\"myfont\" type=\"submit\" name=\"Select\" value=\"Send Selection\">\n";
  }

print <<TBL_32;
</td>
</tr>
TBL_32

  print <<TBL_33;
</table>
</form>
<p align="left" class=\"myfont\">
<input type="button" value="Close" onClick="window.close()">
</p>
TBL_33
  print $cgi->end_html;
}

sub delSession {
  # cek if session is passed to server
  CGI::Session->name($SSID);
  my $session = CGI::Session->load("driver:File", undef, {Directory=>SESIDIR})
                or die CGI::Session->errstr;
  $session->delete();
  $session->flush();

  # force client to remove the cookie
  &gotoLogin('logout',$SSID);
}

sub gotoLogin {
  my ($status,$sid) = @_;
  my $cookie = CGI::cookie(-name=>$sid,-value=>'',-expires=>LOGOUTEXP);
  $status = LOGINPAGE . "?status=$status";
  print CGI::header(-type=>"text/html",-location=>$status,-cookie=>$cookie);
  exit;
}

sub dienice {
  my ($msg) = @_;
  # clear cookie
  my $cookie = CGI::cookie(-name=>$SSID,-value=>'',-expires=>LOGOUTEXP);
  print CGI::header(-type=>"text/html",-cookie=>$cookie);
  print CGI::start_html("Error");
  print "<h2>Error</h2>\n";
  print "<p>$msg</p>";
  print CGI::end_html;
  exit;
}

sub dbdie {
  my ($package, $filename, $line) = caller;
  my ($errmsg) = "Database error: $DBI::errstr<br>\n called from $package $filename line $line";
  &dienice($errmsg);
}

sub formatNumber {
  my ($number) = @_;
  for ( my $i = -3; $i > -1 * length($number); $i -= 4 )
  {
    substr( $number, $i, 0 ) = ',';
  }
  return $number;
}

1;

