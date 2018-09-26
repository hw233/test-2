/**
 * Created on 2017-03-30
 * @Author: huangluyu(huangluyu@ice-time.cn)
 * @Brief : cdata_loader python/c API封装
 */

#include <Python.h>
#include <string.h>
#include "loader.h"

using namespace std;

static Loader *g_loader = NULL;

static PyObject *_build_pyobj(const char *value, int type)
{
    PyObject *ret = NULL;

    if (type == TYPE_INT32) {
        ret = PyInt_FromLong(strtol(value, NULL, 10));
    } else if (type == TYPE_SINGLE) {
        ret = PyFloat_FromDouble(strtod(value, NULL));
    } else if (type == TYPE_STRING) {
        ret = PyString_FromString(value);
    } else if (type == TYPE_INT32_ARRAY) {
        ret = PyList_New(0);
        char *str = (char*)malloc((strlen(value)+1) * sizeof(char));
        strcpy(str, value);

        char *p, *s = str;
        while ((p = strtok_r(s, "#", &s))) {
            PyObject *node = PyInt_FromLong(strtol(p, NULL, 10));
            PyList_Append(ret, node);
            Py_XDECREF(node);
        }

        free(str);
    } else if (type == TYPE_SINGLE_ARRAY) {
        ret = PyList_New(0);
        char *str = (char*)malloc((strlen(value)+1) * sizeof(char));
        strcpy(str, value);

        char *p, *s = str;
        while ((p = strtok_r(s, "#", &s))) {
            PyObject *node = PyFloat_FromDouble(strtod(p, NULL));
            PyList_Append(ret, node);
            Py_XDECREF(node);
        }

        free(str);
    } else if (type == TYPE_STRING_ARRAY) {
        ret = PyList_New(0);
        char *str = (char*)malloc((strlen(value)+1) * sizeof(char));
        strcpy(str, value);

        char *p, *s = str;
        while ((p = strtok_r(s, "#", &s))) {
            PyObject *node = PyString_FromString(p);
            PyList_Append(ret, node);
            Py_XDECREF(node);
        }

        free(str);
    } else if (type == TYPE_BOOLEAN) {
        ret = strcmp(value, "true") == 0 ? PyBool_FromLong(1) : PyBool_FromLong(0);
    }

    if (!ret)
        Py_RETURN_NONE;

    return ret;
}

static PyObject *_build_dict(const vector<string> &data, const char *sheet, const char *key)
{
    PyObject *ret = PyDict_New();

    int i = 0;
    for (const auto &d : data) {
        int type = g_loader->attr_type(sheet, key, i);
        string name = g_loader->attr_name(sheet, key, i);
        PyObject *obj = _build_pyobj(d.c_str(), type);

        int pos = name.find(".");
        if (pos != -1) {
            string sub_class = name.substr(0, pos);
            string sub_name = name.substr(pos + 1);
            
            PyObject *sub_dict = PyDict_GetItemString(ret, sub_class.c_str());
            if (!sub_dict) {
                sub_dict = PyDict_New();
                PyDict_SetItemString(sub_dict, sub_name.c_str(), obj);
                PyDict_SetItemString(ret, sub_class.c_str(), sub_dict);
                Py_XDECREF(sub_dict);
            } else {
                PyDict_SetItemString(sub_dict, sub_name.c_str(), obj);
                PyDict_SetItemString(ret, sub_class.c_str(), sub_dict);
            }
        } else {
            PyDict_SetItemString(ret, name.c_str(), obj);
        }
        Py_XDECREF(obj);
        ++i;
    }

    return ret;
}

static PyObject *init(PyObject *self, PyObject *args)
{
    char *conf, *version;
    if (!PyArg_ParseTuple(args, "ss", &conf, &version))
        return NULL;

    if (!g_loader) {
        g_loader = new Loader(conf, version);
    }

    if (!g_loader) {
        PyErr_SetString(PyExc_Exception, "Init failed");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *load(PyObject *self, PyObject *args)
{
    if (!g_loader) {
        PyErr_SetString(PyExc_Exception, "Data loader isn't initialized");
        return NULL;
    }

    int ret = g_loader->load();

    switch (ret) {
        case SUCCEED: break;
        case ECSV_KEY_NOT_IN_ATTR:
            PyErr_SetString(PyExc_Exception, "Key not found in sheet");
            return NULL;
            break;
        case ECSV_ATTR_REPEAT:
            PyErr_SetString(PyExc_Exception, "Attribute name repeat");
            return NULL;
            break;
        case ECSV_ATTR_NUM:
            PyErr_SetString(PyExc_Exception, "Csv file isn't a matrix");
            return NULL;
            break;
        case ECSV_CANNT_OPEN_FILE:
            PyErr_SetString(PyExc_Exception, "Can't open data file");
            return NULL;
            break;
        case ECSV_BAD_TYPE:
            PyErr_SetString(PyExc_Exception, "Bad data type");
            return NULL;
            break;
        case ECONF_KEY_LEN:
            PyErr_SetString(PyExc_Exception, "Keys len < 1");
            return NULL;
            break;
        case ECONF_NONE_NAME:
            PyErr_SetString(PyExc_Exception, "Sheet's name is none'");
            return NULL;
            break;
        case ECONF_BAD_JSON:
            PyErr_SetString(PyExc_Exception, "Bad json file");
            return NULL;
            break;
        case ECONF_CANNT_OPEN_FILE:
            PyErr_SetString(PyExc_Exception, "Can't open config file");
            return NULL;
            break;
        case ECONF_SHEETS_LEN:
            PyErr_SetString(PyExc_Exception, "Sheets len < 1");
            return NULL;
            break;
        default:
            PyErr_SetString(PyExc_Exception, "Unknow error");
            return NULL;
            break;
    }
    Py_RETURN_NONE;
}

static PyObject *get(PyObject *self, PyObject *args)
{
    char *sheet, *key;
    if (!PyArg_ParseTuple(args, "ss", &sheet, &key))
        return NULL;

    if (!g_loader) {
        PyErr_SetString(PyExc_Exception, "Data loader isn't initialized");
        return NULL;
    }

    const vector<string> &data = g_loader->get(sheet, key);
    PyObject *ret = _build_dict(data, sheet, key);
    
    return ret;
}

static PyObject *get_keys(PyObject *self, PyObject *args)
{
    char *sheet;
    if (!PyArg_ParseTuple(args, "s", &sheet))
        return NULL;

    if (!g_loader) {
        PyErr_SetString(PyExc_Exception, "Data loader isn't initialized");
        return NULL;
    }

    PyObject *ret = PyList_New(0);
    vector<const char*> keys = g_loader->get_keys(sheet);
    int key_type = g_loader->key_type(sheet);
    int i = 0;
    for (const auto &key : keys) {
        PyObject *node = _build_pyobj(key, key_type);
        PyList_Append(ret, node);
        Py_XDECREF(node);
        ++i;
    }

    return ret;
}

static PyObject *destroy(PyObject *self, PyObject *args)
{
    if (g_loader) {
        delete g_loader;
        g_loader = NULL;
    }

    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"init", init, METH_VARARGS},
    {"load", load, METH_VARARGS},
    {"destroy", destroy, METH_VARARGS},
    {"get", get, METH_VARARGS},
    {"get_keys", get_keys, METH_VARARGS},
    {NULL, NULL}
};

extern "C"
void initcdata_loader()
{
    Py_InitModule("cdata_loader", methods);
}
