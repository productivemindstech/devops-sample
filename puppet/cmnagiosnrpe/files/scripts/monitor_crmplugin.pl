#!/usr/bin/perl
use strict;
use warnings;
use feature qw(switch say);

my @count = `mysql -h cm-db-lprod01.audience.local -ujirareader -pjirareader -e "use jiradb7; select ( select  count(TIME_TO_SEC(TIMEDIFF(now(),START_TIME))) from rundetails where JOB_ID like '%com.go2group.jira.plugin.crm.cronservice%')as a" 2>&1`;
if ($count[2] > 1)
{
  print "CRITICAL - CRM Query returning multiple values";
  exit(2);
}
elsif($count[2] == 0)
{
  print "CRITICAL - CRM Query doesn't return any value";
}
else
{
 my @output = `mysql -h cm-db-lprod01.audience.local -ujirareader -pjirareader -e "use jiradb7; select ( select TIME_TO_SEC(TIMEDIFF(now(),START_TIME)) from rundetails where JOB_ID like '%com.go2group.jira.plugin.crm.cronservice%') as a;" 2>&1`;
 if ($output[2] )
  {
   my $secsincelastrun =  $output[2];
   chomp $secsincelastrun;
   my $alerttimeout = 60 ;
    if ($secsincelastrun > $alerttimeout){
     print "CRITICAL - The CRM Plugin last ran $secsincelastrun seconds ago. It should run every 60 seconds."; 
     exit(2);
    } 
    else {
     print "OK - The CRM Plugin last ran $secsincelastrun seconds ago. This is fine as it should run every 60 seconds.\n";
     exit(0);
    }	
  }
 else 
  {
   print "CRITICAL - CRM Query doesn't return any value";
   exit(2);
   }
}  
