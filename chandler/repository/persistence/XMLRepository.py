
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, re, cStringIO, xml.sax.saxutils

from xml.sax import parseString
from datetime import datetime
from struct import pack, unpack
from sys import exc_info
from threading import currentThread, RLock

from model.util.UUID import UUID
from model.item.Item import Item
from model.item.ItemRef import ItemRef, ItemStub, RefDict, TransientRefDict
from model.persistence.Repository import Repository, RepositoryError
from model.persistence.Repository import OnDemandRepository, Store
from model.persistence.Repository import OnDemandRepositoryView

from bsddb.db import DBEnv, DB, DBError
from bsddb.db import DB_CREATE, DB_BTREE, DB_TXN_NOWAIT
from bsddb.db import DB_RECOVER, DB_RECOVER_FATAL
from bsddb.db import DB_INIT_MPOOL, DB_INIT_LOCK, DB_INIT_TXN, DB_DIRTY_READ
from bsddb.db import DBRunRecoveryError, DBNoSuchFileError, DBNotFoundError
from dbxml import XmlContainer, XmlDocument, XmlValue
from dbxml import XmlQueryContext, XmlUpdateContext


class XMLRepository(OnDemandRepository):
    """A Berkeley DBXML based repository.

    This simple repository implementation saves all items in separate XML
    item files in a given directory. It can then load them back to restore
    the same exact item hierarchy."""

    def __init__(self, dbHome):
        'Construct an XMLRepository giving it a DBXML container pathname'
        
        super(XMLRepository, self).__init__(dbHome)

        self._env = None
        self._ctx = XmlQueryContext()
        
    def create(self, verbose=False, notxn=False):

        if not self.isOpen():
            super(XMLRepository, self).create(verbose)
            self._notxn = notxn
            self._create()
            self._status |= self.OPEN

    def _create(self):

        if not os.path.exists(self.dbHome):
            os.makedirs(self.dbHome)
        elif not os.path.isdir(self.dbHome):
            raise ValueError, "%s exists but is not a directory" %(self.dbHome)
        else:
            def purge(arg, path, names):
                for f in names:
                    if f.startswith('__') or f.startswith('log.'):
                        f = os.path.join(path, f)
                        if not os.path.isdir(f):
                            os.remove(f)
            os.path.walk(self.dbHome, purge, None)
        
        self._env = DBEnv()
        if self._notxn:
            self._env.open(self.dbHome, DB_CREATE | DB_INIT_MPOOL, 0)
        else:
            self._env.open(self.dbHome, self.OPEN_FLAGS, 0)

        self._openDb(True)

    def open(self, verbose=False, create=False, notxn=False):

        if not self.isOpen():
            super(XMLRepository, self).open(verbose)
            self._notxn = notxn
            self._env = DBEnv()

            try:
                if self._notxn:
                    self._env.open(self.dbHome, DB_INIT_MPOOL, 0)
                    self._openDb(False)

                else:
                    try:
                        before = datetime.now()
                        self._env.open(self.dbHome,
                                       DB_RECOVER | self.OPEN_FLAGS, 0)
                        after = datetime.now()
                        print 'opened db with recovery in %s' %(after - before)
                        self._openDb(False)

                    except DBRunRecoveryError:
                        before = datetime.now()
                        self._env.open(self.dbHome,
                                       DB_RECOVER_FATAL | self.OPEN_FLAGS, 0)
                        after = datetime.now()
                        print 'opened db with fatal recovery in %s' %(after -
                                                                      before)
                        self._openDb(False)

            except DBNoSuchFileError:
                if create:
                    self._create()
                else:
                    raise

            self._status |= self.OPEN

    def _openDb(self, create):

        txn = None
        
        try:
            if self._notxn:
                txn = None
            else:
                txn = self._env.txn_begin(None, DB_DIRTY_READ | DB_TXN_NOWAIT)
                
            self._refs = XMLRepository.refContainer(self, "__refs__",
                                                    txn, create)
            self._versions = XMLRepository.verContainer(self, "__versions__",
                                                        txn, create)
            self._store = XMLRepository.xmlContainer(self, "__data__",
                                                     txn, create)
        finally:
            if txn is not None:
                txn.commit()

    def close(self, purge=False):

        if self.isOpen():
            self._refs.close()
            self._versions.close()
            self._store.close()
            self._env.close()
            self._env = None
            self._status &= ~self.OPEN

    def _createView(self):

        return XMLRepositoryView(self)

    OPEN_FLAGS = DB_CREATE | DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_TXN

    class xmlContainer(Store):

        def __init__(self, repository, name, txn, create):

            super(XMLRepository.xmlContainer, self).__init__()
        
            self.repository = repository
            self._xml = XmlContainer(repository._env, name)
            self._filename = name
            self.version = "%d.%d.%d" %(self._xml.get_version_major(),
                                        self._xml.get_version_minor(),
                                        self._xml.get_version_patch())
            
            if create:
                self._xml.open(txn, DB_CREATE | DB_DIRTY_READ)
                self._xml.addIndex(txn, "", "uuid",
                                   "node-attribute-equality-string")
                self._xml.addIndex(txn, "", "kind",
                                   "node-element-equality-string")
                self._xml.addIndex(txn, "", "container",
                                   "node-element-equality-string")
                self._xml.addIndex(txn, "", "name",
                                   "node-element-equality-string")
            else:
                self._xml.open(txn, DB_DIRTY_READ)

        def loadItem(self, view, uuid):

            view.ctx.setVariableValue("uuid", XmlValue(uuid.str64()))

            if self.version == "1.1.0":
                results = self._xml.queryWithXPath(view._txn,
                                                   "/item[@uuid=$uuid]",
                                                   view.ctx, DB_DIRTY_READ)
                try:
                    return results.next(view._txn).asDocument()
                except StopIteration:
                    return None

            if self.version == "1.1.1":
                for value in self._xml.queryWithXPathExpression(view._txn,
                                                                view.uuidExpr,
                                                                DB_DIRTY_READ):
                    return value.asDocument()

                return None

            raise ValueError, "dbxml %s not supported" %(self.version)
            
        def loadChild(self, view, uuid, name):

            view.ctx.setVariableValue("name", XmlValue(name.encode('utf-8')))
            view.ctx.setVariableValue("uuid", XmlValue(uuid.str64()))

            if self.version == "1.1.0":
                results = self._xml.queryWithXPath(view._txn,
                                                   "/item[container=$uuid and name=$name]",
                                                   view.ctx, DB_DIRTY_READ)
                try:
                    return results.next(view._txn).asDocument()
                except StopIteration:
                    return None

            if self.version == "1.1.1":
                for value in self._xml.queryWithXPathExpression(view._txn,
                                                                view.containerExpr,
                                                                DB_DIRTY_READ):
                    return value.asDocument()

                return None

            raise ValueError, "dbxml %s not supported" %(self.version)

        def loadroots(self, view):

            ctx = XmlQueryContext()
            ctx.setReturnType(XmlQueryContext.ResultDocuments)
            ctx.setEvaluationType(XmlQueryContext.Lazy)
            ctx.setVariableValue("uuid", XmlValue(Repository.ROOT_ID.str64()))
            nameExp = re.compile("<name>(.*)</name>")

            if self.version == "1.1.0":
                results = self._xml.queryWithXPath(view._txn,
                                                   "/item[container=$uuid]",
                                                   ctx, DB_DIRTY_READ)
                try:
                    while True:
                        xml = results.next(view._txn).asDocument()
                        xmlString = xml.getContent()
                        match = nameExp.match(xmlString,
                                              xmlString.index("<name>"))
                        name = match.group(1)

                        if not name in view._roots:
                            view._loadXML(xml)
                except StopIteration:
                    return

            if self.version == "1.1.1":
                for value in self._xml.queryWithXPath(view._txn,
                                                      "/item[container=$uuid]",
                                                      ctx, DB_DIRTY_READ):
                    xml = value.asDocument()
                    xmlString = xml.getContent()
                    match = nameExp.match(xmlString, xmlString.index("<name>"))
                    name = match.group(1)

                    if not name in view._roots:
                        view._loadXML(xml)

                return

            raise ValueError, "dbxml %s not supported" %(self.version)

        def deleteDocument(self, view, doc):

            self._xml.deleteDocument(view._txn, doc, view.updateCtx)

        def putDocument(self, view, doc):

            self._xml.putDocument(view._txn, doc, view.updateCtx)

        def close(self):

            self._xml.close()
            self._xml = None

        def parseXML(self, xml, handler):

            parseString(xml.getContent(), handler)
            
        def getUUID(self, xml):

            xmlString = xml.getContent()
            index = xmlString.index('uuid=') + 6

            return UUID(xmlString[index:xmlString.index('"', index)])

    class dbContainer(object):

        def __init__(self, repository, name, txn, create):

            super(XMLRepository.dbContainer, self).__init__()

            self.repository = repository
            self._db = DB(repository._env)
            self._filename = name
            
            if create:
                self._db.open(filename = name, dbtype = DB_BTREE,
                              flags = DB_CREATE | DB_DIRTY_READ,
                              txn = txn)
            else:
                self._db.open(filename = name, dbtype = DB_BTREE,
                              flags = DB_DIRTY_READ,
                              txn = txn)

        def close(self):

            self._db.close()
            self._db = None

        def put(self, view, key, value):

            self._db.put(key, value, txn=view._txn)

        def delete(self, view, key):

            try:
                self._db.delete(key, txn=view._txn)
            except DBNotFoundError:
                pass

        def get(self, view, key):

            return self._db.get(key, txn=view._txn)

        def cursor(self, view):

            return self._db.cursor(txn=view._txn)

    class refContainer(dbContainer):

        def deleteItem(self, view, item):

            cursor = None
            
            try:
                cursor = self._db.cursor(txn=view._txn)
                key = item.getUUID()._uuid

                try:
                    val = cursor.set_range(key)
                    while val is not None and val[0].startswith(key):
                        cursor.delete()
                        val = cursor.next()
                except DBNotFoundError:
                    pass

            finally:
                if cursor is not None:
                    cursor.close()

    class verContainer(dbContainer):

        def __init__(self, repository, name, txn, create):

            super(XMLRepository.verContainer, self).__init__(repository, name,
                                                             txn, create)
            if create:
                self._db.put(Repository.ROOT_ID._uuid, pack('>L', 0), txn)

            self.lock = RLock()

        def incrementVersion(self, view, uuid):

            try:
                self.lock.acquire()
                version, = unpack('>I', self.get(view, uuid._uuid))
                version += 1
                self.put(view, uuid._uuid, pack('>I', version))
            finally:
                self.lock.release()

            return version

        def setVersion(self, view, uuid, version):

            self.put(view, uuid._uuid, pack('>I', version))

        def getVersion(self, view, uuid):

            version = self.get(view, uuid._uuid)
            if version is None:
                return None
            
            return unpack('>I', version)[0]

        def deleteVersion(self, view, uuid):

            self.delete(view, uuid._uuid)


class XMLRepositoryView(OnDemandRepositoryView):

    def __init__(self, repository):

        super(XMLRepositoryView, self).__init__(repository)

        self._log = []
        self._txn = None

    def getVersion(self, uuid):

        return self.repository._versions.getVersion(self, uuid)

    def _getCtx(self):

        try:
            return self._ctx

        except AttributeError:
            self._ctx = XmlQueryContext()
            self._ctx.setReturnType(XmlQueryContext.ResultDocuments)
            self._ctx.setEvaluationType(XmlQueryContext.Lazy)

            return self._ctx

    def _getUpdateCtx(self):

        try:
            return self._updateCtx

        except AttributeError:
            self._updateCtx = XmlUpdateContext(self.repository._store._xml)

            return self._updateCtx

    def _getUUIDExpr(self):

        try:
            return self._uuidExpr
        except AttributeError:
            xml = self.repository._store._xml
            xpath = "/item[@uuid=$uuid]"
            self._uuidExpr = xml.parseXPathExpression(None, xpath,
                                                      self.ctx)
            return self._uuidExpr

    def _getContainerExpr(self):

        try:
            return self._containerExpr
        except AttributeError:
            xml = self.repository._store._xml
            xpath = "/item[container=$uuid and name=$name]"
            self._containerExpr = xml.parseXPathExpression(None, xpath,
                                                           self.ctx)
            return self._containerExpr

    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return XMLRefDict(self, item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)

    def getRoots(self):
        'Return a list of the roots in the repository.'

        self.repository._store.loadroots(self)
        return super(XMLRepositoryView, self).getRoots()

    def logItem(self, item):
        
        if super(XMLRepositoryView, self).logItem(item):
            self._log.append(item)
            return True
        
        return False

    def commit(self):
        
        repository = self.repository
        before = datetime.now()
        count = 0
        
        try:
            if not repository._notxn:
                self._txn = repository._env.txn_begin(None, (DB_DIRTY_READ |
                                                             DB_TXN_NOWAIT))
            else:
                self._txn = None

            if self._log:
                count = len(self._log)
                store = repository._store
                versions = repository._versions
                newVersion = versions.incrementVersion(self,
                                                       Repository.ROOT_ID)
                                                                     
                for item in self._log:
                    self._saveItem(item, newVersion, store, versions,
                                   repository.verbose)

        except:
            if self._txn:
                self._txn.abort()
                self._txn = None
            raise

        else:
            if self._txn:
                self._txn.commit()
                self._txn = None

            if self._log:
                for item in self._log:
                    item._setSaved(newVersion)
                del self._log[:]

            after = datetime.now()
            print 'committed %d items in %s' %(count, after - before)

    def _saveItem(self, item, newVersion, store, versions, verbose):

        uuid = item.getUUID()
        if item.isNew():
            version = None

        else:
            version = versions.getVersion(self, uuid)
            if version is None:
                raise ValueError, 'no version for %s' %(item.getItemPath())
            else:
                if version > item._version:
                    raise ValueError, '%s is out of date' %(item.getItemPath())
                oldDoc = store.loadItem(self, uuid)
                if oldDoc is not None:
                    store.deleteDocument(self, oldDoc)

        if item.isDeleted():

            del self._deletedRegistry[uuid]
            if version is not None:
                if verbose:
                    print 'Removing', item.getItemPath()
                self.repository._refs.deleteItem(self, item)
                versions.deleteVersion(self, uuid)

        else:
            if verbose:
                print 'Saving', item.getItemPath()

            out = cStringIO.StringIO()
            generator = xml.sax.saxutils.XMLGenerator(out, 'utf-8')
            generator.startDocument()
            item._saveItem(generator, newVersion)
            generator.endDocument()

            doc = XmlDocument()
            doc.setContent(out.getvalue())
            out.close()
            store.putDocument(self, doc)
            versions.setVersion(self, uuid, newVersion)
            
    ctx = property(_getCtx)
    updateCtx = property(_getUpdateCtx)
    uuidExpr = property(_getUUIDExpr)
    containerExpr = property(_getContainerExpr)
    

class XMLRefDict(RefDict):

    class _log(list):

        def append(self, value):
            if len(self) == 0 or value != self[-1]:
                super(XMLRefDict._log, self).append(value)


    def __init__(self, repository, item, name, otherName):
        
        self._log = XMLRefDict._log()
        self._item = None
        self._uuid = UUID()
        self.view = repository
        self._deletedRefs = {}
        
        super(XMLRefDict, self).__init__(item, name, otherName)

    def _getRepository(self):

        return self.view

    def _loadRef(self, key):

        if self.view is not self.view.repository.view:
            raise RepositoryError, 'current thread is not owning thread'

        if key in self._deletedRefs:
            return None

        self._key.truncate(32)
        self._key.seek(0, 2)
        self._key.write(key._uuid)

        value = self.view.repository._refs.get(self.view, self._key.getvalue())
        if value is None:
            return None

        self._value.truncate(0)
        self._value.seek(0)
        self._value.write(value)
        self._value.seek(0)
        uuid = UUID(self._value.read(16))
        previous = self._readValue()
        next = self._readValue()
        alias = self._readValue()
        
        return (key, uuid, previous, next, alias)

    def _changeRef(self, key):

        if not self.view.isLoading():
            self._log.append((0, key))
        
        super(XMLRefDict, self)._changeRef(key)

    def _removeRef(self, key, _detach=False):

        if not self.view.isLoading():
            self._log.append((1, key))
            self._deletedRefs[key] = key
        else:
            raise ValueError, 'detach during load'

        super(XMLRefDict, self)._removeRef(key, _detach)

    def _writeRef(self, key, uuid, previous, next, alias):

        self._key.truncate(32)
        self._key.seek(0, 2)
        self._key.write(key._uuid)

        self._value.truncate(0)
        self._value.seek(0)
        self._value.write(uuid._uuid)
        self._writeValue(previous)
        self._writeValue(next)
        self._writeValue(alias)
        value = self._value.getvalue()
            
        self.view.repository._refs.put(self.view, self._key.getvalue(), value)

    def _writeValue(self, value):
        
        if isinstance(value, UUID):
            self._value.write('\0')
            self._value.write(value._uuid)

        elif isinstance(value, str) or isinstance(value, unicode):
            self._value.write('\1')
            self._value.write(pack('>H', len(value)))
            self._value.write(value)

        elif value is None:
            self._value.write('\2')

        else:
            raise NotImplementedError, "value: %s, type: %s" %(value,
                                                               type(value))

    def _readValue(self):

        code = self._value.read(1)

        if code == '\0':
            return UUID(self._value.read(16))

        if code == '\1':
            len, = unpack('>H', self._value.read(2))
            return self._value.read(len)

        if code == '\2':
            return None

        raise ValueError, code

    def _eraseRef(self, key):

        self._key.truncate(32)
        self._key.seek(0, 2)
        self._key.write(key._uuid)

        self.view.repository._refs.delete(self.view, self._key.getvalue())

    def _dbRefs(self):

        self._key.truncate(32)
        cursor = self.view.repository._refs.cursor(self.view)

        try:
            key = self._key.getvalue()
            val = cursor.set_range(key)
        except DBNotFoundError:
            val = None
            
        while val is not None and val[0].startswith(key):
            refName = UUID(val[0][32:])

            self._value.truncate(0)
            self._value.seek(0)
            self._value.write(val[1])
            self._value.seek(0)
            uuid = UUID(self._value.read(16))
            previous = self._readValue()
            next = self._readValue()
            alias = self._readValue()
            yield (refName, uuid, previous, next, alias)
                
            val = cursor.next()

        cursor.close()

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, 'Item is already set'
        
        self._item = item
        if item is not None:
            self._prepareKey(item._uuid, self._uuid)

    def _prepareKey(self, uItem, uuid):

        self._uuid = uuid

        self._key = cStringIO.StringIO()
        self._key.write(uItem._uuid)
        self._key.write(uuid._uuid)

        self._value = cStringIO.StringIO()
            
    def _xmlValues(self, generator, mode):

        if mode == 'save':
            for entry in self._log:
                try:
                    value = self._get(entry[1])
                except KeyError:
                    value = None
    
                if entry[0] == 0:
                    if value is not None:
                        ref = value._value
                        previous = value._previousKey
                        next = value._nextKey
                        alias = value._alias
    
                        uuid = ref.other(self._item).getUUID()
                        self._writeRef(entry[1], uuid, previous, next, alias)
                        
                elif entry[0] == 1:
                    self._eraseRef(entry[1])

                else:
                    raise ValueError, entry[0]
    
            del self._log[:]
            self._deletedRefs.clear()
            
            if len(self) > 0:
                if self._aliases:
                    for key, value in self._aliases.iteritems():
                        generator.startElement('alias', { 'name': key })
                        generator.characters(value.str64())
                        generator.endElement('alias')
                generator.startElement('db', {})
                generator.characters(self._uuid.str64())
                generator.endElement('db')

        elif mode == 'serialize':
            super(XMLRefDict, self)._xmlValues(generator, mode)

        else:
            raise ValueError, mode
