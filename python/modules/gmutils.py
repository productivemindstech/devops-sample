import httplib
import time
from xml.etree import ElementTree

from acibuild.config import TEST_JOB
from acibuild.dirutils import remove_files_by_ext
from acibuild.logutils import debug
from acibuild.requestutils import download_file
from acibuild.jenkinsutils import JenkinsJobBuild, JenkinsServer


class JenkinsJob(JenkinsJobBuild):

    def __init__(self, jobname=None, jenkinsserver=None, token="foobar"):
        super(JenkinsJob, self).__init__(data=None)
        self.jobname = jobname
        self.server = jenkinsserver
        self.api = self.server.api
        self.token = token
        self.hash = None
        self.joburl = None

    def start(self, **params):
        self.hash = self.api.build(self.jobname, token=self.token, **params)
        #self.joburl = self.api.get_build_url(self.jobname, self.hash)

    def wait(self):
        self.currentbuild = self.api.wait(self.jobname, self.hash)
        return self.currentbuild

    @property
    def building(self):
        debug("enter")
        if self.joburl is None:
            self.joburl = self.api.get_build_url(self.jobname, self.hash)
            debug(self.joburl)
        self.refresh(self.api.json_api_request(self.joburl, depth=0))
        return super(JenkinsJob, self).building


class HSNightlyBuild(JenkinsJob):
    def bind_lastbuild(self, baseline=None):
        builds = {}
        debug('enter')
        if baseline:
            job = self.api.job('%s' % (self.jobname))
            buildnumber = job['lastCompletedBuild']['number']
            while True:
                debug('%sjob/%s/%s/artifact/builds.json' % (self.server.url, self.jobname, buildnumber))
                r = self.api.request('%sjob/%s/%s/artifact/builds.json' % (self.server.url,
                                                                           self.jobname, buildnumber))
                if r.status_code == httplib.OK:
                    if baseline in r.text:
                        records = r.json()
                        for record in records:
                            jenkinsbuild = JenkinsJobBuild(record)
                            baseline = jenkinsbuild.params()['BASELINE']
                            build = BuildJob(jenkinsserver=self.server, builddata=jenkinsbuild)
                            build.load_json_data()
                            builds[baseline] = build
                        return builds
                buildnumber = buildnumber - 1


class BuildJob(JenkinsJob):

    build_metadata = {}

    def __init__(self, jobname=None, jenkinsserver=None, builddata=None):
        if builddata:
            super(BuildJob, self).__init__(jobname=builddata.name, jenkinsserver=jenkinsserver)
            self.data = builddata.data
        else:
            super(BuildJob, self).__init__(jobname, jenkinsserver)
        self.build_metadata = None

    def wait_for_replication(self, region):
        if not region:
            return
        if self.replication_hash is None:
            return
        debug("Waiting for build replication")
        self.api.wait('build-image', self.replication_hash)

    def _get_property(self, name):
        if self.build_metadata is None:
            return ""
        if name in self.build_metadata:
            return self.build_metadata[name]
        else:
            return ""

    @property
    def build_label(self):
        return self._get_property('baseline')

    @property
    def manifest(self):
        return self._get_property('manifest')

    @property
    def chip(self):
        return self._get_property('chip')

    @property
    def product(self):
        return self._get_property('product')

    @property
    def defconfig(self):
        return self._get_property('defconfig')

    @property
    def buildpath_region_mv(self):
        return self._get_property('buildpath_region_mv')

    @property
    def buildpath_region_idc(self):
        return self._get_property('buildpath_region_idc')

    @property
    def replication_hash(self):
        if self._get_property('replication_hash') == '':
            return None
        else:
            return self._get_property('replication_hash')

    def load_json_data(self):
        self.build_metadata = {}
        #build_info_file = "C:\\temp\\build-info.json"
        #if os.path.isfile(build_info_file):
        #    fp = open(build_info_file)
        #    self.build_metadata = json.load(fp)
        r = self.api.request('%s/artifact/output/build-info.json' % (self.url, ))
        if r.status_code == httplib.OK:
            self.build_metadata = r.json()
        #FIXME: Build path should come from json
        path = "public/Host_Software/Releases/nightly"
        pid = self.params()['PARENT_BUILD_ID']
        baseline = self.params()['BASELINE']
        self.build_metadata['buildpath_region_idc'] = "//bglfs/%s/%s/%s" % (path, pid, baseline)
        self.build_metadata['buildpath_region_mv'] = "//fs/%s/%s/%s" % (path, pid, baseline)


class MatrixJob(JenkinsJob):

    def __init__(self, jobname, jenkinsserver):
        super(MatrixJob, self).__init__(jobname=jobname, jenkinsserver=jenkinsserver)
#        self.matrix_name = matrix_name
        self.matrixbuilds = {}
        self.completed_builds = {}

    def start(self):
        super(MatrixJob, self).start()
        #self.joburl = "http://cmnagios:8080/job/build-nightly-system/46/"
        #self.hash = '823841967'
        return 0

    def bind_lastbuild(self, matrixlabel=None):
        debug('enter')
        if matrixlabel:
            matrixlabel = 'BASELINE=%s/' % matrixlabel
            job = self.api.job('%s/%s' % (self.jobname, matrixlabel))
            self.joburl = job['lastBuild']['url'].replace(matrixlabel, '')
        else:
            job = self.api.job(self.jobname)
            self.joburl = job['lastBuild']['url']
        print self.joburl

    def pull_completed_jobs(self, axislist=[]):
        debug("enter")
        matrixbuilds = self.api.matrix_job_status(self.joburl)
        self.refresh(self.api.json_api_request(self.joburl, depth=0))
        newly_completed_builds = {}
        for axis in matrixbuilds:
            if axis not in axislist:
                continue
            if matrixbuilds[axis] is not None:
                if not matrixbuilds[axis].building and axis not in self.completed_builds:
                    buildjob = BuildJob(jenkinsserver=self.server, builddata=matrixbuilds[axis])
                    buildjob.load_json_data()
                    self.completed_builds[axis] = buildjob
                    newly_completed_builds[axis] = buildjob
        return newly_completed_builds


class TestJob(JenkinsJob):
    total = 0
    fail = 0

    def __init__(self, test_node, build, label, jobname=TEST_JOB):
        super(TestJob, self).__init__(jobname, jenkinsserver=test_node.server)
        self.build = build
        self.label = label
        self.test_node = test_node

    def trigger_test(self, **params):
        try:
            super(TestJob, self).start(**params)
            return True
        except EnvironmentError, e:
            debug("Failed triggering build: %r" % (e, ))
            return False

    def start_hstest(self):
        try:
            debug('enter')
            super(TestJob, self).start(NODE_LABEL=self.label,
                                       NIGHTLY_BUILD_NUMBER=self.build.number)
            return True
        except EnvironmentError, e:
            debug("Failed triggering build: %r" % (e, ))
            return False

    @property
    def building(self):
        _building = super(TestJob, self).building
        print _building
        if not _building:
            self.download_test_reports()
        return _building

    def download_test_reports(self):
        #FIXME: add unkown status for below attributes
        self.passed = -1
        self.failed = -1
        self.status = 'ERROR'
        jenkinsapi = self.test_node.server.api
        r = jenkinsapi.request('%s/robot/report/output.xml' % (self.url, ))
        if r.status_code == httplib.OK:
            download_file('%s/robot/report/output.xml' % (self.url, ),
                          '%s.xml' % (self.label, ))
            doc = ElementTree.fromstring(r.text.encode('utf-8').strip())
            for stat in doc.findall('statistics/total/stat'):
                if stat.text == "All Tests":
                    self.status = 'SUCCESS'
                    self.passed = int(stat.attrib['pass'])
                    self.failed = int(stat.attrib['fail'])


# class HealthCheckJob(TestJob):
    # script = 'ls'

    # def set_test_node(self):
        # self.parameters['TEST_TYPE'] = 'health-check'


class JenkinsGM(object):
    def __init__(self, clsTest):
        self.servers = {
            "hs-jenkins": JenkinsServer("hs-jenkins", url="http://hs-jenkins/")}
        self.gmserver = self.servers['hs-jenkins']
        remove_files_by_ext(['.xml'])
        self.clsTest = clsTest


    def get_nodes_by_label(self, label):
        nodes = []
        for server in self.servers:
            debug('Search in ' + server)
            for node in self.servers[server].get_nodes_by_label(label):
                nodes.append(node)
        return nodes


    def test_matrix_job(self, axis):
        debug('enter')
        job = MatrixJob(jobname="build-nightly-system", jenkinsserver=self.servers["hs-jenkins"])
        job.bind_lastbuild(axis[0])
        tests = {}
        building = True
        self.all_builds = {}
        while True:
            debug('Still building')
            building = job.building
            builds = job.pull_completed_jobs(axis)
            for label in builds:
                if builds[label].result == 'FAILURE':
                    continue
                test_nodes = self.get_nodes_by_label(label)
                if test_nodes:
                    test_node = test_nodes[0]
                    #test_node = None
                    #builds[label].wait_for_replication(test_node.region)
                    test = TestJob(test_node, builds[label], label)
                    if test.start_hstest():
                        tests[label] = test
            if not building:
                break
            time.sleep(30)

        while True:
            tests_running = False
            for label in tests:
                if tests[label].building:
                    print label + " test still running"
                    tests_running = True
            if not tests_running:
                break
            time.sleep(2)
        print "Builds executed on:"
        for label in job.completed_builds:
            print label
        print "Tests executed on:"
        for label in tests:
            print label
        self.builds = job.completed_builds
        self.tests = tests

    def test_hs_builds(self, axis):
        debug('enter')
        job = HSNightlyBuild(jobname="trigger-nightly-builds", jenkinsserver=self.servers["hs-jenkins"])
        builds = job.bind_lastbuild(axis[0])
        tests = {}
        for label in builds:
            if builds[label].result == 'FAILURE':
                continue
            test_nodes = self.get_nodes_by_label(label)
            if test_nodes:
                test_node = test_nodes[0]
                #test_node = None
                #builds[label].wait_for_replication(test_node.region)
                test = TestJob(test_node, builds[label], label)
                if test.start_hstest():
                    tests[label] = test

        while True:
            tests_running = False
            for label in tests:
                if tests[label].building:
                    print label + " test still running"
                    tests_running = True
            if not tests_running:
                break
            time.sleep(2)
        print "Tests executed on:"
        for label in tests:
            print label
        self.builds = builds
        self.tests = tests

    def test_binaries(self, builds):
        debug('enter')
        tests = {}
        for label in builds:
            test_nodes = self.get_nodes_by_label(label)
            if test_nodes:
                test_node = test_nodes[0]
                #test_node = None
                #builds[label].wait_for_replication(test_node.region)
                test = self.clsTest(test_node, builds[label], label)
                if test.trigger_test():
                    tests[label] = test

        while True:
            tests_running = False
            for label in tests:
                if tests[label].building:
                    print label + " test still running"
                    tests_running = True
            if not tests_running:
                break
            time.sleep(2)
        self.builds = builds
        self.tests = tests
