#!/usr/bin/perl -wT

#
# File Sharing Web Application
#
# get.cgi
# 

use CGI;
use CGI::Carp qw(fatalsToBrowser);
use POSIX qw(strftime);
use lib '.';
use My::Session;

$CGI::DISABLE_UPLOADS   = 0;
$CGI::POST_MAX          = 1024; # 1KB
 
my @fileholder;
my $cgi = new CGI;

my $safe_filename_characters = "a-zA-Z0-9_.-";

if (!$cgi->param('f')) {
  error ($cgi, "You must specify name of the file to download.");
} 
if (!$cgi->param('id')) {
  error ($cgi, "You must specify the id to download.");
}

my $filename = $cgi->param('f');
my $userid   = $cgi->param('id');
my ($fileSize, $fileRange ,$differ, $differ2, $lastMod);

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
  error ($cgi, "Filename contains invalid characters");
}
# check the id
if ($userid =~ /[^\d+]/) {
  error ($cgi, "Id contains invalid characters");
}

if ($filename eq '') { 
  print "Content-type: text/html\n\n"; 
  print "You must specify a file to download."; 
} else {

  open(FH, "<${\UPLOADDIR}/$userid/$filename") || error($cgi, "Error open file or file $filename not found."); 
  ($fileSize) = (stat("${\UPLOADDIR}/$userid/$filename"))[7];
  ($lastMod) = (stat("${\UPLOADDIR}/$userid/$filename"))[9];
  $lastMod = epoch2datetime($lastMod);

  if (exists $ENV{HTTP_RANGE}) {
  
    $fileRange = $& if ($ENV{HTTP_RANGE} =~ /\d+/);
    $differ = $fileSize - $fileRange;  
    $differ2 = $fileSize - 1;  
    print $cgi->header(-status=>"206 Partial Content",
                       -type=>"application/x-download",
                       -Last_Modified=>$lastMod,
                       -Accept_Ranges=>"bytes",
                       -Content_Length=>$differ,
                       -Content_Range=>"bytes $fileRange-$differ2/$fileSize",
                       -Connection=>"close",
                       -Content_Disposition=>"attachment;filename=$filename"
                      );
    seek FH, $fileRange, 1;

  } else {

    print $cgi->header(-status=>"200 OK",
                       -type=>"application/x-download",
                       -Last_Modified=>$lastMod,
                       -Accept_Ranges=>"bytes",
                       -Content_Length=>$fileSize,
                       -Connection=>"close",
                       -Content_Disposition=>"attachment;filename=$filename"
                      );
  }

  while (<FH>) {
    print $_;
  }
  close (FH) || error ($cgi, 'Error close file');
  # save to database
  &saveDownload($userid,$filename);
}

sub error {
  my ($cgi, $reason ) = @_;
  
  print $cgi->header( "text/html" ),
        $cgi->start_html( "Error" ),
        $cgi->h1( "Error" ),
        $cgi->p( "Your download was not procesed because the following error ",
               "occured: " ),
        $cgi->p($cgi->i($reason) ),
        $cgi->end_html;
  exit;
}

sub epoch2datetime {
  my ($epoch) = @_;
  return (strftime "%a, %e %b %Y %H:%M:%S %Z", localtime($epoch));
}
