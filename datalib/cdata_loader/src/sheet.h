/**
 * Created on 2017-03-30
 * @Author: huangluyu(huangluyu@ice-time.cn)
 * @Brief : sheet, 包括单个sheet和复合sheet
 */

#ifndef _SHEET_H_
#define _SHEET_H_

#include <map>
#include <list>
#include <vector>
#include <string>

/*load函数的返回值*/
#define SUCCEED                 0                           //成功
#define ECSV_KEY_NOT_IN_ATTR    101                         //key不在字段中
#define ECSV_ATTR_REPEAT        102                         //字段名重复
#define ECSV_ATTR_NUM           103                         //字段数量不一致
#define ECSV_CANNT_OPEN_FILE    104                         //无法打开csv文件
#define ECSV_BAD_TYPE           105                         //不正确的数据类型
#define ECONF_KEY_LEN           201                         //key的数量小与1
#define ECONF_NONE_NAME         202                         //name为空

#define TYPE_UNKNOW             0
#define TYPE_INT32              1
#define TYPE_SINGLE             2
#define TYPE_STRING             3
#define TYPE_INT32_ARRAY        4
#define TYPE_SINGLE_ARRAY       5
#define TYPE_STRING_ARRAY       6
#define TYPE_BOOLEAN            7

/*单个sheet*/
class SignalSheet {
private:
    std::vector<std::string> names;                         //字段名
    std::vector<int> types;                                 //类型
    std::map<std::string, std::vector<std::string>> data;   //数据 key <-> data

    std::string name;
    std::vector<std::string> key_names;

    int _last_line_len;

    static const std::vector<std::string> empty_vector;
    static const char *empty_str;

    std::vector<std::string> parse_line(std::string line);
    int parse_name(const std::string &line);
    int parse_type(const std::string &line);
    int parse_data(const std::string &line);

public:
    int key_type;

    SignalSheet() : _last_line_len(-1) {}

    SignalSheet(const char *name, const std::vector<std::string> &key_names)
        : name(name), key_names(key_names), _last_line_len(-1)
    {}

    int load(const char *file);

    const std::vector<std::string> &get(const char *key);
    std::vector<std::string> get_keys();
    int attr_type(size_t index);
    std::string attr_name(size_t index);
};

/*复合sheet*/
class ComplexSheet {
private:
    std::map<std::string, SignalSheet*> key_sheet;           //key到signal sheet的映射

    std::string name;
    std::string path;
    std::vector<std::string> sheets;
    std::vector<std::string> key_names;
    bool is_loaded;

    static const std::vector<std::string> empty_vector;
    static const char *empty_str;
public:
    ComplexSheet() {}

    ComplexSheet(const char *name, const char *path,
        const std::vector<std::string> &sheets, const std::vector<std::string> &key_names)
        : name(name), path(path), sheets(sheets), key_names(key_names), is_loaded(false)
    {}
    ~ComplexSheet();

    int load();

    const std::vector<std::string> &get(const char *key);
    std::vector<const char*> get_keys();
    int key_type();
    int attr_type(const char *key, size_t index);
    std::string attr_name(const char *key, size_t index);
};

#endif //_SHEET_H_