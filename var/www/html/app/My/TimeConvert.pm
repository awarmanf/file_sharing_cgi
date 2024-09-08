package My::TimeConvert;

use base qw(Exporter);
use POSIX qw(strftime);
use Time::Local;
use DateTime;
use strict;
our @EXPORT = qw(datetime2epoch strtime2epoch epoch2datetime);
our @EXPORT_OK = qw();

sub datetime2epoch {
  # this sub routine will convert string date to localtime format
  # string date must have format of like "2016-01-06 08:55:49"

  my ($date) = @_;

  my ($sec, $min, $hour);
  my @arr = split(/ /,$date);

  # split date
  my @adate = split (/-/, $arr[0]);
  my $year = $adate[0];
  my $mon  = $adate[1]-1; # must be subtract 1
  my $mday = $adate[2];

  # split hour
  my @ahour = split (/:/, $arr[1]);
  $hour = $ahour[0]; $min = $ahour[1]; $sec = $ahour[2];
  return timelocal($sec, $min, $hour, $mday, $mon, $year);
}

sub strtime2epoch {
  # This sub routine will convert string date to DateTime format (date and time object)
  # String date must have format of like "Fri Dec 16 2016 09:47:48 GMT+0700 (WIB)"

  my ($string) = @_;

  my @arr = split(/\s+/,$string);
  my @amonth = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
  my (@tz, $year, $month, $day, $hour, $min, $sec);
  
  foreach (0..$#amonth) { $month = $_+1 if $amonth[$_] eq $arr[1]; }
  $day  = $arr[2];
  $year = $arr[3];

  # split hour
  my @ahour = split (/:/, $arr[4]);
  $hour = $ahour[0]; $min = $ahour[1]; $sec = $ahour[2];

  @tz = split(/\+/,$arr[5]);
  
  my $dt = DateTime->new(
           year => $year,
           month => $month,
           day   => $day,
           hour => $hour,
           minute => $min,
           second => $sec,
           time_zone => $tz[1]);
  # return datetime value in epoch & mysql time format
  return ($dt->epoch,$dt->strftime ("%F %T"));
}

sub epoch2datetime {
  my ($epoch) = @_;
  # return datetime value in epoch & mysql time format
  return ($epoch, strftime "%F %T", localtime($epoch));
}

1;

