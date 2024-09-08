#!/usr/bin/perl -wT

#
# File Sharing Web Application
#
# index.cgi
#

use strict;
use CGI qw(:standard);
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;

use lib '.';
use My::Session;

$CGI::DISABLE_UPLOADS  = 0;
$CGI::POST_MAX         = 10240;

my $status;
my $message = '';

if ( $ENV{REQUEST_METHOD} eq 'GET' and param('status')) {
  $status = CGI::param('status');

  if ($status eq 'expired') { 
    $message = 'Your session is expired.'; 
  } elsif ($status eq 'empty') { 
    $message = 'Your session is empty.'; 
  } elsif ($status eq 'askinput') { 
    $message = 'Please input username and password.'; 
  } elsif ($status eq 'invalid') { 
    $message = 'Invalid credentials.'; 
  } elsif ($status eq 'cannot') { 
    $message = 'Can not connect to Server Authentication'; 
  } elsif ($status eq 'error') { 
    $message = 'Error in database operation'; 
  } elsif ($status eq 'blocked') { 
    $message = 'Your session has been blocked. Contact administrator.'; 
  } elsif ($status eq 'over') { 
    $message = 'Your quota has been exceeded. Contact administrator.'; 
  } elsif ($status eq 'logout') { 
    $message = 'You have been logout. Thank you.'; 
  } else { 
    $message = ''; }
}

if ( $ENV{REQUEST_METHOD} eq 'POST' ) {

  my $user = CGI::param('username');
  my $pass = CGI::param('password');

  # authenticate this username and password
  &cekLogin($user, $pass);
}

print CGI::header;
print <<HTML;
<!doctype html>
<html lang="en">
<head>
<title>File Sharing Web Application</title>
<meta name="keywords" content="File Sharing Web Application" />
<meta name="Cache-Control" content="no-cache" />
<meta name="copyright" content="awarmanf\@yahoo.com" />
<meta name="robots" content="index,follow" />
<link rel="shortcut icon" href="images/logo.ico">
<link rel="stylesheet" type="text/css" media="screen, projection" href="css/screen.css" />
<link rel="stylesheet"  type="text/css" media="screen, projection" href="css/buttons.screen.css" />
<style type="text/css">
#loginContent { width: 350px; margin: 100px auto; }
button[type] { margin: 0.5em 0; }
</style>
<meta charset="utf-8">
</head>
<body>
<div id="loginContent" class="container">
<p align="left"><img src="images/logo-white.png" alt="Your Company"></p>
<form id="normal" class="general" action="" method="post"> 
  <fieldset>
    <legend>Enter information</legend>
    <p>
    <label for="username">Username</label>
    <br />
    <input type="text" id="username" name="username" class="text" size="20" />
    </p>
    <p>
    <label for="password">Password</label>
    <br />
    <input type="password" id="password" name="password" class="text" size="20" />
    </p>
    <p style='color:red;text-align: center;'>$message</p>
    <p align="center">
    <input title="Submit" alt="Submit" name="submitButton" type="submit" value="Submit" class="submit" /> 
    <input title="Reset" alt="Reset" name="reset" type="reset" value="Reset" />
    </p>
  </fieldset>
</form>
</div>
HTML
print CGI::end_html;
