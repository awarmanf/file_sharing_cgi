#!/usr/bin/perl -wT

#
# File Sharing Web Application
#
# logout.cgi
#

use strict;
use CGI;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use lib '.';
use My::Session;

# cek session
&delSession;

