#!/usr/bin/env python
#
# Copyright 2010 Formspring
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from time import time
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("worker_id", help="globally unique worker_id between 0 and 1023", type=int)


class IDHandler(tornado.web.RequestHandler):
    max_time = int(time() * 1000)
    sequence = 0
    worker_id = False
    epoch = 1259193600000 # 2009-11-26
    
    def get(self):
        curr_time = int(time() * 1000)
        
        if curr_time < self.max_time:
            # stop handling requests til we've caught back up
            raise tornado.web.HTTPError(500, 'Clock went backwards! %d < %d' % (curr_time, self.max_time))
        
        if curr_time > self.max_time:
            self.sequence = 0
            self.max_time = curr_time
        
        self.sequence += 1
        if self.sequence > 4095:
            # Sequence overflow, bail out 
            raise tornado.web.HTTPError(500, 'Sequence Overflow: %d' % self.sequence)
        
        generated_id = ((curr_time - self.epoch) << 22) + (self.worker_id << 12) + self.sequence
        self.set_header("Content-Type", "text/plain")
        self.write(str(generated_id))
        self.flush() # avoid ETag, etc generation 


def main():
    tornado.options.parse_command_line()
    
    if 'worker_id' not in options:
        print 'missing --worker_id argument, see %s --help' % sys.argv[0] 
        sys.exit()
    
    if not 0 <= options.worker_id < 1024:
        print 'invalid worker id, must be between 0 and 1023'
        sys.exit()
        
    IDHandler.worker_id = options.worker_id
    
    application = tornado.web.Application([
        (r"/", IDHandler),
    ], static_path="./static")
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
