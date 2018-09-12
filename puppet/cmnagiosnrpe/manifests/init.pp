include 'nsclient'
class cmnagiosnrpe($tool_name=undef,
$purpose_of_tool=undef,
$machine_function=undef,
$primary_contact=undef,
$secondary_contact=undef,
$url=undef,
$cname=undef,
$documentation=undef,
$accounts=undef,
$uptime_criticality=undef,
$licenses=undef,
$integrates_with=undef,
$check_disk=undef,
$related_jobs=undef,
$authorization_type=undef,
$nagios=undef,
$customservice=undef){
   if  $operatingsystem !='windows'and ($nagios == 'Enable' or $nagios == 'Disable_Notification'){
    class { 'nrpe':
	allowed_hosts => ['127.0.0.1', 'cmnagios','cmnagios-dev'],
        dont_blame_nrpe => 1
	}
    
    file { 
    '/etc/nagios/scripts':
    ensure => 'directory',
    source => 'puppet:///modules/cmnagiosnrpe/scripts',
    recurse => 'remote',
    path => '/etc/nagios/scripts/',
    owner => 'root',
    group => 'root',
    mode  => '0755',
    }
    nrpe::command {
    'check_load':
      ensure  => present,
      command => 'check_load -w $ARG1$ -c $ARG2$';
    }
    nrpe::command {
    'check_disk':
      ensure  => present,
      command => 'check_disk -w $ARG1$ -c $ARG2$ -W $ARG3$ -K $ARG4$ -p $ARG5$';
    }
    nrpe::command {
    'check_disk_all':
      ensure  => present,
      command => 'check_disk -w $ARG1$ -c $ARG2$ -e';
    }
    nrpe::command {
    'check_procs':
      ensure  => present,
      command => 'check_procs -w $ARG1$ -c $ARG2$ -s $ARG3$';
    }
    nrpe::command {
    'check_perforce':
      ensure  => present,
      command => '/usr/lib64/nagios/plugins/check_procs -a p4d';
    }
    nrpe::command {
    'check_jira':
      ensure  => present,
      libdir => '/etc/nagios/scripts/',
      command => 'monitor.pl -performance -l /tmp';
    }
    nrpe::command {
    'check_procs_by_arg':
      ensure  => present,
      command => 'check_procs -w $ARG1$ -c $ARG2$ -a $ARG3$ -u $ARG4$';
    }
    nrpe::command {
    'check_puppet':
      ensure  => present,
      command => 'check_procs_by_arg!1:1!1:1!puppet-server-release.jar!puppet';
    }
	
	nrpe::command {
    'check_swap':
      ensure  => present,
      command => 'check_swap -w $ARG1$ -c $ARG2$';
    }
	
	nrpe::command {
    'check_crm':
      ensure  => present,
      libdir => '/etc/nagios/scripts/',
      command => 'monitor_crmplugin.pl ';
   }
}   
    elsif  $operatingsystem =='windows' and ($nagios == 'Enable' or $nagios == 'Disable_Notification'){
     class { 'nsclient':
     package_source_location => 'https://github.com/mickem/nscp/releases/download/0.5.0.62/',
     package_name            => 'NSClient++',
     package_source          => 'NSCP-0.5.0.62-x64.msi',
     allowed_hosts => ['cmnagios','cmnagios-dev']
    }
	}
}
