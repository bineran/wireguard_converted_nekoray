import base64
import os
import sys
import re


# 检查文件是否存在或大小为0，即文件无效
def check_file_exist_or_zero_size(file):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        sys.exit()


# 读取优选ip的ip.txt文件
def read_ip_endpoints(file="ip.txt"):
    endpoints = []
    with open(file, mode='r', encoding='utf-8') as rf:
        for item in rf.readlines():
            if item.strip() != "":
                endpoints.append(item.strip())
        return endpoints


# 读取wg-config.conf配置文件的信息
def read_wireguard_key_parameters(file='配置文件/wg-config.conf'):
    with open(file=file, mode='r', encoding='utf-8') as f:
        wireguard_param = dict()
        for line in f:
            if line:
                if line.startswith("PrivateKey"):
                    wireguard_param["PrivateKey"] = line.strip().replace(' ', '').replace("PrivateKey=", '')
                if line.startswith("PublicKey"):
                    wireguard_param["PublicKey"] = line.strip().replace(' ', '').replace("PublicKey=", '')
                if line.startswith("Address"):
                    wireguard_param["Address"] = line.strip().replace(' ', '').replace("Address=", '').split(',')
                if line.startswith("MTU"):
                    wireguard_param["MTU"] = line.strip().replace(' ', '').replace("MTU=", '')
        return wireguard_param


# 将从配置文件中读取到信息，写入到指定的JSON字符串中
def update_base_info(MTU=None):
    param = read_wireguard_key_parameters()
    peer_public_key = param["PublicKey"].strip()
    private_key = param["PrivateKey"].strip()
    IPv4 = param["Address"][0].strip()
    IPv6 = param["Address"][1].strip()
    MTU = param["MTU"].strip() if MTU is None else MTU
    nekoray_str_json = '{"_v":0,"addr":"127.0.0.1","cmd":[""],"core":"internal","cs":"{\\n  \\"interface_name\\": ' \
                       '\\"WARP\\",\\n  \\"local_address\\": [\\n    \\"#IPv4地址\\",\\n    \\"#IPv6地址\\"\\n  ],\\n' \
                       '  \\"mtu\\": #MUT值,\\n  \\"peer_public_key\\": \\"#peer_public_key\\",\\n  \\"private_key\\":' \
                       ' \\"#private_key\\",\\n  \\"server\\": \\"IP地址\\",\\n  \\"server_port\\": 端口,\\n  ' \
                       '\\"system_interface\\": false,\\n  \\"tag\\": \\"proxy\\",\\n  \\"type\\": \\"wireguard' \
                       '\\"\\n}","mapping_port":0,"name":"别名","port":1080,"socks_port":0}'
    update_key = nekoray_str_json.replace('#peer_public_key', peer_public_key).replace('#private_key', private_key)
    update_address = update_key.replace('#IPv4地址', IPv4).replace('#IPv6地址', IPv6).replace('#MUT值', MTU)
    return update_address


# 判断是否为IP地址（IPv4或IPv6）
def is_ip_address(ip_addr):
    """ 匹配 IPv4 和 IPv6 地址 """
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    ipv6_pattern = r'^(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:))$'
    try:
        addr = ip_addr.rsplit(":", 1)[0]
        ip = addr[1:-1] if addr.startswith('[') and addr.endswith(']') else addr
        port = ip_addr.rsplit(':', 1)[1] if ip_addr.count(":") == 1 or (
                ip_addr.count(":") > 3 and "]:" in ip_addr) else None
        if re.match(ipv4_pattern, ip) and (port.isdigit() and int(port) >= 80):
            ipv4 = re.match(ipv4_pattern, ip).group(0)
            return True
        elif re.match(ipv6_pattern, ip) and (port.isdigit() and int(port) >= 80):
            ipv6 = re.match(ipv6_pattern, ip).group(0)
            return True
    except Exception as e:
        pass


if __name__ == '__main__':
    """判断文件是否存在或文件的大小为0"""
    files = ["配置文件/wg-config.conf", "ip.txt"]
    for file in files:
        check_file_exist_or_zero_size(file)  # 检查文件是否存在
    """程序正式启动"""
    while True:
        input_mut = input("是否修改MTU值(默认是配置文件中的值，可用的取值范围1280~1500)：")
        if (input_mut.isdigit() and 1280 <= int(input_mut) <= 1500) or input_mut.strip() == '':
            break
    input_country = input('添加节点名称或别名的前缀吗？(比如，CN)：').strip()
    country = f'{input_country.strip()}_' if input_country != '' else ''
    base_str = None
    if input_mut.isdigit():
        base_str = update_base_info(MTU=input_mut)  # 调用函数
    else:
        base_str = update_base_info()  # 调用函数
    endpoints = read_ip_endpoints(file=files[1])
    output_file = 'ouput_node.txt'  # nekoray节点保存到这里
    f = open(output_file, mode='w', encoding='utf-8')
    for endpoint in endpoints:
        ip = endpoint.rsplit(':', 1)[0]
        ip = ip[1:-1] if ip.startswith('[') and ip.endswith(']') else ip  # 针对IPv6地址，写入JSON的server中要去掉中括号
        port = endpoint.rsplit(':', 1)[1]
        remarks = f"{ip}:{port}" if ip.count(":") == 0 else f"[{ip}]:{port}"  # 节点的别名、节点的名称（不重要，ipv6的加上中括号）
        node = base_str.replace('别名', f'{country}{remarks}').replace('IP地址', ip).replace('端口', port)
        encoded = base64.b64encode(node.encode('utf-8'), altchars=b'-_')
        encoded_str = str(encoded, encoding='utf-8')
        transport_protocol = "nekoray://custom#"  # 在base64编码好的字符串前缀添加这个前缀（NekoBox软件专用的前缀）
        nekoray_node = transport_protocol + encoded_str
        # print(nekoray_node)
        f.write(f"{nekoray_node}\n")
        f.flush()
    print(f"已经将节点写入{output_file}文件中了.")
    f.close()
    os.system("pause")
