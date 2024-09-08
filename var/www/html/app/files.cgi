#!/usr/bin/perl -w

#
# File Sharing Web Application
#
# files.cgi
#

use strict;
use CGI;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use lib '.';
use My::Session;

$CGI::DISABLE_UPLOADS   = 0;
$CGI::POST_MAX         = 10240;

# session validation
&cekSession;

my $cgi = new CGI;
my @names = ();
my $status = '';

if ( $ENV{REQUEST_METHOD} eq 'POST' and $cgi->param('name') and $cgi->param('Delete')) {
  @names = $cgi->param('name'); $status = 'Delete';
}

if ( $ENV{REQUEST_METHOD} eq 'POST' and $cgi->param('name') and $cgi->param('Select')) {
  @names = $cgi->param('name'); $status = 'Select';
}

&myFiles($userid,\@names,$status);

