/**
 * Created on 2017-03-30
 * @Author: huangluyu(huangluyu@ice-time.cn)
 * @Brief : loader 类
 */

#ifndef _LOADER_H_
#define _LOADER_H_

#include <map>
#include <list>
#include <string>
#include <json/json.h>
#include "sheet.h"

#define ECONF_BAD_JSON 203  //错误的json格式
#define ECONF_CANNT_OPEN_FILE 204 //无法打开conf文件
#define ECONF_SHEETS_LEN 205 //sheets长度小与1

class Loader {
private:
    std::string conf;
    std::string version;
    bool is_loaded;
    std::map<std::string, ComplexSheet*> sheets;

    std::vector<std::string> jsonvalue2vector(const Json::Value &value);

    static const std::vector<std::string> empty_vector;
    static const char *empty_str;
public:
    Loader(const char *conf, const char *version)
        : conf(conf), version(version), is_loaded(false)
    {}
    ~Loader();

    int load();
    const std::vector<std::string> &get(const char *sheet, const char *key);
    std::vector<const char*> get_keys(const char *sheet);
    int key_type(const char *sheet);
    int attr_type(const char *sheet, const char *key, size_t index);
    std::string attr_name(const char *sheet, const char *key, size_t index);
};

#endif //_LOADER_H_