"""
Tests for the utility functions.

Pyro - Python Remote Objects.  Copyright by Irmen de Jong.
irmen@razorvine.net - http://www.razorvine.net/python/Pyro
"""

import unittest

import sys, imp, os
import Pyro.util
import Pyro.config

if not hasattr(imp,"reload"):
    imp.reload=reload   # python 2.5 doesn't have imp.reload

def crash(arg=100):
    pre1="black"
    pre2=999
    def nest(p1,p2):
        s="white"+pre1 #@UnusedVariable
        x=pre2 #@UnusedVariable
        y=arg//2 #@UnusedVariable
        p3=p1//p2
        return p3
    a=10
    b=0
    s="hello" #@UnusedVariable
    c=nest(a,b)
    return c

class TestUtils(unittest.TestCase):

    def testFormatTracebackNormal(self):
        try:
            crash()
        except:
            tb="".join(Pyro.util.formatTraceback(detailed=False))
            self.assertTrue("p3=p1//p2" in tb)
            self.assertTrue("ZeroDivisionError" in tb)
            self.assertFalse(" a = 10" in tb)
            self.assertFalse(" s = 'whiteblack'" in tb)
            self.assertFalse(" pre2 = 999" in tb)
            self.assertFalse(" x = 999" in tb)

    def testFormatTracebackDetail(self):
        try:
            crash()
        except:
            tb="".join(Pyro.util.formatTraceback(detailed=True))
            self.assertTrue("p3=p1//p2" in tb)
            self.assertTrue("ZeroDivisionError" in tb)
            if sys.platform!="cli":
                self.assertTrue(" a = 10" in tb)
                self.assertTrue(" s = 'whiteblack'" in tb)
                self.assertTrue(" pre2 = 999" in tb)
                self.assertTrue(" x = 999" in tb)


    def testPyroTraceback(self):
        try:
            crash()
        except:
            pyro_tb=Pyro.util.formatTraceback(detailed=True)
            if sys.platform!="cli":
                self.assertTrue(" Extended stacktrace follows (most recent call last)\n" in pyro_tb)
        try:
            crash("stringvalue")
        except Exception:
            x=sys.exc_info()[1] 
            setattr(x, Pyro.constants.TRACEBACK_ATTRIBUTE, pyro_tb)
            pyrotb="".join(Pyro.util.getPyroTraceback())
            self.assertTrue("Remote traceback" in pyrotb)
            self.assertTrue("crash(\"stringvalue\")" in pyrotb)
            self.assertTrue("TypeError:" in pyrotb)
            self.assertTrue("ZeroDivisionError" in pyrotb)
            delattr(x, Pyro.constants.TRACEBACK_ATTRIBUTE)
            pyrotb="".join(Pyro.util.getPyroTraceback())
            self.assertFalse("Remote traceback" in pyrotb)
            self.assertFalse("ZeroDivisionError" in pyrotb)
            self.assertTrue("crash(\"stringvalue\")" in pyrotb)
            self.assertTrue("TypeError:" in pyrotb)
            
    def testPyroTracebackArgs(self):
        try:
            crash()
        except Exception:
            ex_type, ex_value, ex_tb = sys.exc_info()
            x=ex_value
            tb1=Pyro.util.getPyroTraceback()
            tb2=Pyro.util.getPyroTraceback(ex_type, ex_value, ex_tb)
            self.assertEqual(tb1, tb2)
            tb1=Pyro.util.formatTraceback()
            tb2=Pyro.util.formatTraceback(ex_type, ex_value, ex_tb)
            self.assertEqual(tb1, tb2)
            tb2=Pyro.util.formatTraceback(detailed=True)
            if sys.platform!="cli":
                self.assertNotEqual(tb1, tb2)
            # old call syntax, should get an error now:
            self.assertRaises(TypeError, Pyro.util.getPyroTraceback, x)
            self.assertRaises(TypeError, Pyro.util.formatTraceback, x)

    def testSerialize(self):
        ser=Pyro.util.Serializer()
        before=(42, ["a","b","c"], {"henry": 998877, "suzie": 776655})
        data,c=ser.serialize(before,compress=False)
        after=ser.deserialize(data)
        self.assertEqual(before,after)
        self.assertEqual(bool,type(c))
        data,c=ser.serialize(before,compress=True)
        after=ser.deserialize(data,compressed=c)
        self.assertEqual(before,after)
        self.assertEqual(bool,type(c))

    def testSerializeCompression(self):
        smalldata=["wordwordword","blablabla","orangeorange"]
        largedata=["wordwordword"+str(i) for i in range(30)]
        ser=Pyro.util.Serializer()
        data1,compressed=ser.serialize(smalldata,compress=False)
        self.assertFalse(compressed)
        data2,compressed=ser.serialize(smalldata,compress=True)
        self.assertFalse(compressed, "small messages should not be compressed")
        self.assertEquals(len(data1),len(data2))
        data1,compressed=ser.serialize(largedata,compress=False)
        self.assertFalse(compressed)
        data2,compressed=ser.serialize(largedata,compress=True)
        self.assertTrue(compressed, "large messages should be compressed")
        self.assertTrue(len(data1)>len(data2))


    def testConfig(self):
        def clearEnv():
            if "PYRO_HOST" in os.environ: del os.environ["PYRO_HOST"]
            if "PYRO_NS_PORT" in os.environ: del os.environ["PYRO_NS_PORT"]
            if "PYRO_COMPRESSION" in os.environ: del os.environ["PYRO_COMPRESSION"]
            imp.reload(Pyro.config)
        clearEnv()
        try:
            self.assertEqual(9090, Pyro.config.NS_PORT)
            self.assertEqual("localhost", Pyro.config.HOST)
            self.assertEqual(False, Pyro.config.COMPRESSION)
            os.environ["NS_PORT"]="4444"
            imp.reload(Pyro.config)
            self.assertEqual(9090, Pyro.config.NS_PORT)
            os.environ["PYRO_NS_PORT"]="4444"
            os.environ["PYRO_HOST"]="something.com"
            os.environ["PYRO_COMPRESSION"]="OFF"
            imp.reload(Pyro.config)
            self.assertEqual(4444, Pyro.config.NS_PORT)
            self.assertEqual("something.com", Pyro.config.HOST)
            self.assertEqual(False, Pyro.config.COMPRESSION)
        finally:
            clearEnv()
            self.assertEqual(9090, Pyro.config.NS_PORT)
            self.assertEqual("localhost", Pyro.config.HOST)
            self.assertEqual(False, Pyro.config.COMPRESSION)

    def testResolveAttr(self):
        class Test(object):
            def __init__(self,value):
                self.value=value
            def __str__(self):
                return "<%s>" % self.value
        obj=Test("obj")
        obj.a=Test("a")
        obj.a.b=Test("b")
        obj.a.b.c=Test("c")
        obj.a._p=Test("p1")
        obj.a._p.q=Test("q1")
        obj.a.__p=Test("p2")
        obj.a.__p.q=Test("q2")
        #check the method with dotted disabled 
        self.assertEquals("<a>",str(Pyro.util.resolveDottedAttribute(obj,"a",False)))
        self.assertRaises(AttributeError, Pyro.util.resolveDottedAttribute, obj, "a.b",False)
        self.assertRaises(AttributeError, Pyro.util.resolveDottedAttribute, obj, "a.b.c",False)
        self.assertRaises(AttributeError, Pyro.util.resolveDottedAttribute, obj, "a.b.c.d",False)
        self.assertRaises(AttributeError, Pyro.util.resolveDottedAttribute, obj, "a._p",False)
        self.assertRaises(AttributeError, Pyro.util.resolveDottedAttribute, obj, "a._p.q",False)
        self.assertRaises(AttributeError, Pyro.util.resolveDottedAttribute, obj, "a.__p.q",False)
        #now with dotted enabled
        self.assertEquals("<a>",str(Pyro.util.resolveDottedAttribute(obj,"a",True)))
        self.assertEquals("<b>",str(Pyro.util.resolveDottedAttribute(obj,"a.b",True)))
        self.assertEquals("<c>",str(Pyro.util.resolveDottedAttribute(obj,"a.b.c",True)))
        self.assertRaises(AttributeError,Pyro.util.resolveDottedAttribute, obj,"a.b.c.d",True)   # doesn't exist
        self.assertRaises(AttributeError,Pyro.util.resolveDottedAttribute, obj,"a._p",True)    #private
        self.assertRaises(AttributeError,Pyro.util.resolveDottedAttribute, obj,"a._p.q",True)    #private
        self.assertRaises(AttributeError,Pyro.util.resolveDottedAttribute, obj,"a.__p.q",True)    #private

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
