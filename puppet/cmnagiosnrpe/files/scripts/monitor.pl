#!/usr/bin/env perl
use strict;
use warnings;

=pod

=head1 NAME JIRAUp.pl

Connect to JIRA and verify that it's up and functioning.

=head1 VERSION

=over

=item Author

Andrew DeFaria <Andrew@ClearSCM.com>

=item Revision

$Revision: #2 $

=item Created

Wed Apr  1 14:11:20 PDT 2015

=item Modified

$Date: 2017/06/09 $

=back

=head1 SYNOPSIS

  $ JIRAUp.pl [-jiraserver <server>] 
              [-use|rname <username>] [-pa|ssword <password>]
              [-j|iraserver <jiraserver>]
              [-pe|rformance] [-i|ssues <n>] [-t|oolong <n>]
              [-l|ogpath <path>]
              [-v|erbose] [-h|elp] [-u|sage]

  Where:

    -v|erbose:         Display progress output
    -h|elp:            Display full help
    -usa|ge:           Display usage
    -use|rname:        Username to log into JIRA with (Default: jira-admin)
    -pa|ssword:        Password to log into JIRA with (Default: jira-admin's 
                       password)
    -j|iraserver:      Machine where Jira lives (Default: jira)
    -[no]pe|rformance: Whether to perform performance testing
    -i|ssues:          How many Devops issues to retrieve for performanceTest
                       (Default: 100)
    -t|oolong:         How many seconds would be considered too long 
                       (Default: 60 seconds)
    -l|ogpath:         Where to put the log file (Default: $TMP)

=head1 DESCRIPTION

This script will simply connect to jira and verify it's up and running.

=cut

use FindBin;
use lib "$FindBin::Bin/../../lib";

local $| = 1;

use JIRAUtils;
use Display;
use Utils;
use Logger;

use Getopt::Long; 
use Pod::Usage;

our %opts = (
  verbose     => $ENV{VERBOSE}    || sub { set_verbose },
  debug       => $ENV{DEBUG}      || sub { set_debug },
  usage       => sub { pod2usage },
  help        => sub { pod2usage (-verbose => 2)},
  jiraserver  => $ENV{JIRASERVER} || 'jira',
  username    => 'jira-admin',
  password    => 'jira-admin',
  issues      => 100,
  toolong     => 30,
  performance => 1,
  logpath     => $ENV{TMP},
);

my $log;

sub getPerformanceData () {
  my @lines = ReadFile $log->fullname;
  
  my $average;
  
  $average += $_ for @lines;
  
  return int ($average / scalar @lines); 
} # getPerformanceData

sub performanceTest () {
  verbose 'Starting performanceTest';
  
  my $start = time;
  
  my $issues = getIssues ('project = devops', 0, $opts{issues});
  
  return time() - $start;
} # performanceTest

sub main () {
  GetOptions (
    \%opts,
    'verbose',
    'debug',
    'usage',
    'help',
    'jiraserver=s',
    'username=s',
    'password=s',
    'performance!',
    'issues=i',
    'toolong=i',
    'logpath=s',
  ) or pod2usage;

  $opts{debug}   = get_debug   if ref $opts{debug}   eq 'CODE';
  $opts{verbose} = get_verbose if ref $opts{verbose} eq 'CODE';
  
  $log = Logger->new (
    path   => $opts{logpath},
    append => 1,
  );

  verbose "Connecting to $opts{username}\@$opts{jiraserver}";
  
  Connect2JIRA ($opts{username}, $opts{password}, $opts{jiraserver})
    or die "CRITICAL: Unable to connect to $opts{jiraserver}\n";

  verbose 'Getting issue DEVOP-666';
  
  my $issue = getIssue ('DEVOP-666');
  
  if ($issue) {
    verbose "$opts{jiraserver} seems to be up and running";
    
    display "OK - JIRA server is up";
  } else {
    die "CRITICAL: Unable to talk to $opts{jiraserver}\n";
  } # if
  
  if ($opts{performance}) {
    my $time = performanceTest;
    $log->msg ($time);
    
    my $average = getPerformanceData;
      
    my @loadAvgs        = LoadAvg();
    my $performanceData = "loadavg_1min=$loadAvgs[0], "
                        . "loadavg_5min=$loadAvgs[1], "
                        . "loadavg_16min=$loadAvgs[2], "
                        . "retrieval_time=$time, "
                        . "average_retrieval_time=$average";
                        
    if ($time > $opts{toolong}) {
      die "CRITICAL: JIRA seems to be running slowly - "
        . "It took $time seconds to retrieve $opts{issues} Devops issues "
        . "when it should take less than $opts{toolong}|$performanceData\n";
    } else {
      display "OK - JIRA performance is acceptable|$performanceData";
    } # if
  } # if
  
  return 0;
} # main

exit main;
