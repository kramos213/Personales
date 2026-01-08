def run_module(module_execute_func, hosts, user, password):
    results = {}
    for host in hosts:
        try:
            output = module_execute_func(host, user, password)
            results[host] = ("success", output)
        except Exception as e:
            results[host] = ("error", str(e))
    return results
