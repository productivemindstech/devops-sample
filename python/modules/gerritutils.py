import httplib
import json

import requests
#from requests.auth import HTTPDigestAuth

session = requests.session()
#session.auth = HTTPDigestAuth(GERRIT_USERNAME, GERRIT_PASSWORD)
session.auth = (GERRIT_USERNAME, GERRIT_PASSWORD)
session.headers.update({'Content-Type': 'application/json',
                        'Accept': 'text/plain'})


class GerritReview(object):
    def __init__(self):
        self.change_number = None
        self.revision_id = None
        self.message = None
        self.comments = {}
        self.labels = {}

    def set_change(self, change_number, revision_id):
        self.change_number = change_number
        self.revision_id = revision_id

    def set_message(self, message):
        self.message = message

    def add_comment(self, filename, line, message):
        self.comments.setdefault(filename, []).append(dict(line=line,
                                                           message=message))

    def add_label(self, name, value):
        self.labels[name] = value

    def get_post_url(self):
        # POST /changes/{change-id}/revisions/{revision-id}/review
        # See http://gerrit-hs/Documentation/rest-api-changes.html#change-id
        return '%sa/changes/%s/revisions/%s/review' % (
            GERRIT_API_ENDPOINT, self.change_number, self.revision_id)

    def post(self):
        data = {}
        if self.message:
            data['message'] = self.message
        if self.comments:
            data['comments'] = self.comments
        if self.labels:
            data['labels'] = self.labels
        url = self.get_post_url()
        debug("Posting Gerrit review: %s %s" % (url, data))
        r = session.post(url, data=json.dumps(data))
        text = r.text
        if text.startswith(")]}\'\n"):
            text = text[5:]
        if r.status_code != httplib.OK:  # pragma: nocoverage
            raise Exception((url, r.status_code, text))
        return json.loads(text)


if __name__ == '__main__':  # pragma: nocoverage
    review = GerritReview()
    review.set_change("4392",
                      "648d899a6e924925c5e0eebffb830c2afe65bf2d")
    review.set_message("\n".join([
        "* Foo #1 http://foobar.com/1\n",
        "* Foo #2 http://foobar.com/2\n",
    ]))
    review.add_comment("Makefile", 53, "Yay")
    review.add_label("Verified", 1)
    print review.post()
