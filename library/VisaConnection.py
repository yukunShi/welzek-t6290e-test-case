import visa


class VisaConnection(object):
    def __init__(self, resource_name, tmo=10000):

        self._rm = None
        self._conn = None

        # try default backend
        if self.resource_manager() or self.resource_manager('/usr/lib/librsvisa.so') or self.resource_manager('@py'):
            self.open_resource(resource_name, tmo)
        else:
            raise Exception('Can not Open resource, please check py-visa backend')

    def resource_manager(self, backend=""):
        try:
            self._rm = visa.ResourceManager(backend)
            return self._rm

        except OSError:
            return None
        except ValueError:
            return None

    def open_resource(self, name, tmo):
        if self._rm:
            self._conn = self._rm.open_resource(name)
            self._conn.timeout = tmo

    def write(self, msg, termination=None):
        self._conn.write(msg, termination)

    def read(self):
        return self._conn.read()

    def query(self, msg):
        return self._conn.query(msg)

    def query_ieee_block(self, msg, datatype='h', container=list):
        return self._conn.query_binary_values(msg, datatype=datatype, container=container)
