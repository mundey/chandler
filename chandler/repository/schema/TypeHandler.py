
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.util.uuid import UUID
from repository.util.Path import Path
from repository.util.SingleRef import SingleRef
from repository.util.ClassLoader import ClassLoader


class TypeHandler(object):

    def typeHandler(cls, view, value):

        try:
            for t in cls.typeHandlers[view][type(value)]:
                if t.recognizes(value):
                    return t
        except KeyError:
            pass

        from repository.item.Item import Item
        if isinstance(value, Item):
            return cls.typeHandlers[view][SingleRef][0]

        try:
            typeKind = cls.typeHandlers[view][None]
        except KeyError:
            print type(value), value
            raise
        
        types = typeKind.findTypes(value)
        if types:
            return types[0]
            
        raise TypeError, 'No handler for values of type %s' %(type(value))

    def makeString(cls, view, value):

        return cls.typeHandler(view, value).makeString(value)

    def makeValue(cls, typeName, data):

        try:
            return cls.typeDispatch[typeName](data)
        except KeyError:
            raise ValueError, "Unknown type %s for data: %s" %(typeName, data)

    def hashValue(cls, view, value):

        return cls.typeHandler(view, value).hashValue(value)

    def clear(cls, view):

        try:
            cls.typeHandlers[view].clear()
        except KeyError:
            pass


    typeHandler = classmethod(typeHandler)
    makeString = classmethod(makeString)
    makeValue = classmethod(makeValue)
    hashValue = classmethod(hashValue)
    clear = classmethod(clear)

    typeHandlers = {}
    typeDispatch = {
        'str': str,
        'unicode': unicode,
        'uuid': UUID,
        'path': Path,
        'ref': lambda(data): SingleRef(UUID(data)),
        'bool': lambda(data): data != 'False',
        'int': int,
        'long': long,
        'float': float,
        'complex': complex,
        'class': lambda(data): ClassLoader.loadClass(data),
        'none': lambda(data): None,
    }
