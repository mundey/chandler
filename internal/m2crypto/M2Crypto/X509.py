"""M2Crypto wrapper for OpenSSL X509 API.

This module has evolved based on the needs of supporting X.509 
certificate operations (mainly attribute getters for 
authentication purposes) from within an SSL connection.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved.

Open Source Applications Foundation (OSAF) has extended the functionality
to make it possible to create certificates programmatically.

Epydoc comments started by OSAF.

OSAF Changes copyright (c) 2004 Open Source Applications Foundation.
Author: Heikki Toivonen
"""

RCS_id='$Id$'

# M2Crypto
import ASN1, BIO, Err
import m2

class X509Error(Exception): pass

m2.x509_init(X509Error)

V_OK = m2.X509_V_OK


class X509_Extension:
    """
    X509 extension.

    XXX Does not allow copying from existing extension.
    """
    def __init__(self, name, value, critical=0, _pyfree=1):
        self.x509_ext = m2.x509v3_ext_conf(None, None, name, value)
        self.set_critical(critical)
        self._pyfree = _pyfree

    def __del__(self):
        if self._pyfree:
            m2.x509_extension_free(self.x509_ext)

    def _ptr(self):
        return self.x509_ext

    def set_critical(self, critical=1):
        """
        Mark this extension critical or noncritical. By default an
        extension is not critical.

        @type critical:  int
        @param critical: Nonzero sets this extension as critical. Calling
                         this method without arguments will set this extension
                         to critical.
        """
        return m2.x509_extension_set_critical(self.x509_ext, critical)

    def get_critical(self):
        """
        Return whether or not this is a critical extension.

        @rtype:   int
        @return:  Nonzero if this is a critical extension.
        """
        return m2.x509_extension_get_critical(self.x509_ext)

    def get_name(self):
        """
        Get the extension name, for example 'subjectAltName'.
        """
        return m2.x509_extension_get_name(self.x509_ext)

    def get_value(self):
        """
        Get the extension value, for example 'DNS:www.example.com'.
        """
        buf=BIO.MemoryBuffer()
        m2.x509_ext_print(buf.bio_ptr(), self.x509_ext, 0, 0)
        return buf.read_all()


class X509_Extension_Stack:
    def __init__(self, stack=None, _pyfree=0):
        if stack is not None:
            self.stack = stack
            self._pyfree = _pyfree
        else:
            self.stack = m2.sk_x509_extension_new_null()
            self._pyfree = 1
        self._refkeeper = {}

    def __del__(self):
        if self._pyfree:
            m2.sk_x509_extension_free(self.stack)

    def __len__(self):
        return m2.sk_x509_extension_num(self.stack)

    def __getitem__(self, idx):
        if idx < 0 or idx >= m2.sk_x509_extension_num(self.stack):
            raise IndexError

        ret = X509_Extension('foo', 'bar') # XXX Need 'copy constructor'
        m2.x509_extension_free(ret.x509_ext)
        ret.x509_ext = m2.sk_x509_extension_value(self.stack, idx)
        ret._pyfree = 0
        return ret
        
    def _ptr(self):
        return self.stack

    def push(self, x509_ext):
        self._refkeeper[x509_ext._ptr()] = x509_ext
        return m2.sk_x509_extension_push(self.stack, x509_ext._ptr())

    def pop(self):
        x509__ext_ptr = m2.sk_x509_extension_pop(self.stack)
        del self._refkeeper[x509_ext_ptr]


class X509_Store_Context:
    def __init__(self, x509_store_ctx, _pyfree=0):
        self.ctx = x509_store_ctx
        self._pyfree = _pyfree

    #def __del__(self):
    # XXX verify this method
    #    m2.x509_store_ctx_cleanup(self.ctx)


class X509_Name:

    nid = {'C'  : m2.NID_countryName,
           'SP' : m2.NID_stateOrProvinceName,
           'L'  : m2.NID_localityName,
           'O'  : m2.NID_organizationName,
           'OU' : m2.NID_organizationalUnitName,
           'CN' : m2.NID_commonName,
           'Email' : m2.NID_pkcs9_emailAddress,
           'emailAddress': m2.NID_pkcs9_emailAddress}

    def __init__(self, x509_name=None, _pyfree=0):
        if x509_name is not None:
            assert m2.x509_name_type_check(x509_name), "'x509_name' type error"
            self.x509_name = x509_name
            self._pyfree = _pyfree
        else:
            self.x509_name = m2.x509_name_new()
            self._pyfree = 1

    def __del__(self):
        try:
            if self._pyfree:
                m2.x509_name_free(self.x509_name)
        except AttributeError:
            pass

    def __str__(self):
        assert m2.x509_name_type_check(self.x509_name), "'x509_name' type error" 
        return m2.x509_name_oneline(self.x509_name)

    def __getattr__(self, attr):
        if attr in self.nid.keys():
            assert m2.x509_name_type_check(self.x509_name), "'x509_name' type error" 
            return m2.x509_name_by_nid(self.x509_name, self.nid[attr])
        else:
            raise AttributeError, (self, attr)

    def __setattr__(self, attr, value):
        if attr in self.nid.keys():
            assert m2.x509_name_type_check(self.x509_name), "'x509_name' type error"
            return m2.x509_name_set_by_nid(self.x509_name, self.nid[attr], value)
        else:
            self.__dict__[attr] = value


class X509:

    """
    Object interface to an X.509 digital certificate.
    """

    def __init__(self, x509=None, _pyfree=0):
        if x509 is not None:
            assert m2.x509_type_check(x509), "'x509' type error"
            self.x509 = x509
            self._pyfree = _pyfree
        else:
            self.x509 = m2.x509_new()
            self._pyfree = 1

    def __del__(self):
        try:
            if self._pyfree:
                m2.x509_free(self.x509)
        except AttributeError:
            pass

    def _ptr(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return self.x509

    def as_text(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        buf=BIO.MemoryBuffer()
        m2.x509_print(buf.bio_ptr(), self.x509)
        return buf.read_all()

    def as_der(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        buf=BIO.MemoryBuffer()
        m2.i2d_x509(buf.bio_ptr(), self.x509)
        return buf.read_all()

    def as_pem(self):
        """
        as_pem
        """
        buf=BIO.MemoryBuffer()
        m2.x509_write_pem(buf.bio_ptr(), self.x509)
        return buf.read_all()

    def save_pem(self, filename):
        """
        save_pem
        """
        bio=BIO.openfile(filename, 'wb')
        return m2.x509_write_pem(bio.bio_ptr(), self.x509)

    def get_version(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return m2.x509_get_version(self.x509)

    def set_version(self, version):
        """
        Set version.

        @type version:  int
        @param version: Version number.
        @rtype:         int
        @return:        Returns 0 on failure.
        """
        assert m2.x509_type_check(self.x509), "'x509' type error"    
        return m2.x509_set_version(self.x509, version)

    def get_serial_number(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        asn1_integer = m2.x509_get_serial_number(self.x509)
        return m2.asn1_integer_get(asn1_integer)

    def set_serial_number(self, serial):
        """
        Set serial number. Every certificate must have a serial number.
        A CA must issue unique serial numbers for all the certificates that
        it issues.

        @type serial:   int
        @param serial:  Serial number.
        """
        assert m2.x509_type_check(self.x509), "'x509' type error"
        # This "magically" changes serial since asn1_integer is C pointer
        # to x509's internal serial number.
        asn1_integer = m2.x509_get_serial_number(self.x509)
        return m2.asn1_integer_set(asn1_integer, serial)
        # XXX Or should I do this?
        #asn1_integer = m2.asn1_integer_new()
        #m2.asn1_integer_set(asn1_integer, serial)
        #return m2.x509_set_serial_number(self.x509, asn1_integer)

    def get_not_before(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return ASN1.ASN1_UTCTIME(m2.x509_get_not_before(self.x509))

    def get_not_after(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return ASN1.ASN1_UTCTIME(m2.x509_get_not_after(self.x509))

    # XXX We should have method(s) here to set and adjust notBefore/After.

    def get_pubkey(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return m2.x509_get_pubkey(self.x509)

    def set_pubkey(self, pkey):
        """
        Set the public key for the certificate

        @type pkey:  EVP_PKEY
        @param pkey: Public key
        """
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return m2.x509_set_pubkey(self.x509, pkey.pkey)

    def get_issuer(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return X509_Name(m2.x509_get_issuer_name(self.x509))

    def set_issuer(self, name):
        """
        Set issuer name.

        @type name:     X509_Name
        @param name:    subjectName field.
        """
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return m2.x509_set_issuer_name(self.x509, name.x509_name)

    def get_subject(self):
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return X509_Name(m2.x509_get_subject_name(self.x509))

    def set_subject(self, name):
        """
        Set subject name.

        @type name:     X509_Name
        @param name:    subjectName field.
        """
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return m2.x509_set_subject_name(self.x509, name.x509_name)

    def add_ext(self, ext):
        """
        Add X509 extension to this certificate.

        @type ext:     X509_Extension
        @param ext:    Extension
        """
        assert m2.x509_type_check(self.x509), "'x509' type error"
        return m2.x509_add_ext(self.x509, ext.x509_ext, -1)

    def get_ext(self, name):
        """
        Get X509 extension by name.

        @type name:    Name of the extension
        @param name:   str
        @return:       X509_Extension
        """
        for i in range(self.get_ext_count()):
            ext = self.get_ext_at(i)
            if ext.get_name() == name:
                return ext

    def get_ext_at(self, index):
        """
        Get X509 extension by index.

        @type index:    Name of the extension
        @param index:   int
        @return:        X509_Extension
        """
        if index < 0 or index >= self.get_ext_count():
            raise IndexError
        
        ret = X509_Extension('foo', 'bar') # XXX We need 'copy constructor'
        m2.x509_extension_free(ret.x509_ext)
        ret.x509_ext = m2.x509_get_ext(self.x509, index)
        ret._pyfree = 0
        return ret

    def get_ext_count(self):
        """
        Get X509 extension count.
        """
        return m2.x509_get_ext_count(self.x509)        

    def sign(self, pkey, md):
        """
        Sign the certificate.

        @type pkey:  EVP_PKEY
        @param pkey: Public key
        @type md:    string
        @param md:   Message digest algorithm to use for signing, for example
                     'sha1'.
        """
        assert m2.x509_type_check(self.x509), "'x509' type error"        
        mda = getattr(m2, md)
        if not mda:
            raise ValueError, ('unknown message digest', md)
        return m2.x509_sign(self.x509, pkey.pkey, mda())

def load_cert(file):
    bio = BIO.openfile(file)
    return load_cert_bio(bio)


def load_cert_bio(bio):
    return X509(m2.x509_read_pem(bio._ptr()), 1)


class X509_Store:
    def __init__(self, store=None, _pyfree=0):
        if store is not None:
            self.store = store
            self._pyfree = _pyfree
        else:
            self.store = m2.x509_store_new()
            self._pyfree = 1

    def __del__(self):
        if self._pyfree:
            m2.x509_store_free(self.store)

    def _ptr(self):
        return self.store

    def load_info(self, file):
        m2.x509_store_load_locations(self.store, file)

    load_locations = load_info
         
    def add_x509(self, x509):
        assert isinstance(x509, X509)
        return m2.x509_store_add_cert(self.store, x509._ptr())


class X509_Stack:
    def __init__(self, stack=None, _pyfree=0):
        if stack is not None:
            self.stack = stack
            self._pyfree = _pyfree
        else:
            self.stack = m2.sk_x509_new_null()
            self._pyfree = 1
        self._refkeeper = {}

    def __del__(self):
        if self._pyfree:
            m2.sk_x509_free(self.stack)

    def __len__(self):
        return m2.sk_x509_num(self.stack)

    def __getitem__(self, idx):
        if idx < 0 or idx >= m2.sk_x509_num(self.stack):
            raise IndexError, 'index out of range'
        v=m2.sk_x509_value(self.stack, idx)
        return X509(v)

    def _ptr(self):
        return self.stack

    def push(self, x509):
        assert isinstance(x509, X509)
        self._refkeeper[x509._ptr()] = x509
        return m2.sk_x509_push(self.stack, x509._ptr())

    def pop(self):
        x509_ptr = m2.sk_x509_pop(self.stack)
        del self._refkeeper[x509_ptr]


class Request:
    """
    An X509 certificate request. A request is required to make a certificate.
    """
    def __init__(self, req=None, _pyfree=0):
        if req is not None:
            self.req = req
            self._pyfree = _pyfree
        else:
            self.req = m2.x509_req_new()
            self._pyfree = 1

    def __del__(self):
        if self._pyfree:
            m2.x509_req_free(self.req)

    def as_text(self):
        buf=BIO.MemoryBuffer()
        m2.x509_req_print(buf.bio_ptr(), self.req)
        return buf.read_all()

    def as_pem(self):
        buf=BIO.MemoryBuffer()
        m2.x509_req_write_pem(buf.bio_ptr(), self.req)
        return buf.read_all()

    def save_pem(self, filename):
        bio=BIO.openfile(filename, 'wb')
        return m2.x509_req_write_pem(bio.bio_ptr(), self.req)

    def get_pubkey(self):
        """
        Get the public key for the request.

        @rtype:      EVP_PKEY
        @return:     Public key from the request.
        """
        return m2.x509_req_get_pubkey(self.req)

    def set_pubkey(self, pkey):
        """
        Set the public key for the request.

        @type pkey:  EVP_PKEY
        @param pkey: Public key
        """
        return m2.x509_req_set_pubkey(self.req, pkey.pkey)

    def get_subject(self):
        return X509_Name(m2.x509_req_get_subject_name(self.req))

    def set_subject(self, name):
        """
        Set subject name.

        @type name:     X509_Name
        @param name:    subjectName field.
        """
        return m2.x509_req_set_subject_name(self.req, name.x509_name)

    def get_version(self):
        """
        Get version.

        @rtype:         int
        @return:        Returns version.
        """
        return m2.x509_req_get_version(self.req)

    def set_version(self, version):
        """
        Set version.

        @type version:  int
        @param version: Version number.
        @rtype:         int
        @return:        Returns 0 on failure.
        """
        return m2.x509_req_set_version(self.req, version)

    def add_extensions(self, ext_stack):
        """
        Add X509 extensions to this request.

        @type ext_stack:  X509_Extension_Stack
        @param ext_stack: Stack of extensions to add.
        """
        return m2.x509_req_add_extensions(self.req, ext_stack._ptr())

    def verify(self, pkey):
        return m2.x509_req_verify(self.req, pkey)

    def sign(self, pkey, md):
        mda = getattr(m2, md)
        if not mda:
            raise ValueError, ('unknown message digest', md)
        return m2.x509_req_sign(self.req, pkey.pkey, mda())

def load_request(pemfile):
    f=BIO.openfile(pemfile)
    cptr=m2.x509_req_read_pem(f.bio_ptr())
    f.close()
    if cptr is None:
        raise Err.get_error()
    return Request(cptr, 1)


class CRL:
    def __init__(self, crl=None, _pyfree=0):
        if crl is not None:
            self.crl = crl
            self._pyfree = _pyfree
        else:
            self.crl = m2.x509_crl_new()
            self._pyfree = 1

    def __del__(self):
        if self._pyfree:
            m2.x509_crl_free(self.crl)

    def as_text(self):
        buf=BIO.MemoryBuffer()
        m2.x509_crl_print(buf.bio_ptr(), self.crl)
        return buf.read_all()

def load_crl(pemfile):
    f=BIO.openfile(pemfile)
    cptr=m2.x509_crl_read_pem(f.bio_ptr())
    f.close()
    if cptr is None:
        raise Err.get_error()
    return CRL(cptr, 1)


