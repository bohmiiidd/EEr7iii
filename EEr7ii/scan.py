import sys
import subprocess

def perform_scan(target, scan_type, verbose=False):
    command = ['nmap']
    if verbose:
        command.append('-vvv')
    
    if scan_type == 'nmap':
        command.extend([target])
    elif scan_type == 'version_scanner':
        command.extend(['-sV', target])
    elif scan_type == 'vuln_scanner':
        command.extend(['--script', 'vuln', target])
    elif scan_type == 'aggressive_scan':
        command.extend(['-A', target])
    else:
        raise ValueError("Unsupported scan type")

    try:
        output = subprocess.check_output(command, text=True)
    except subprocess.CalledProcessError as e:
        output = e.output
    return output

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python scan.py <target> <scan_type> [--verbose]")
        sys.exit(1)
    
    target = sys.argv[1]
    scan_type = sys.argv[2]
    verbose = '--verbose' in sys.argv

    result = perform_scan(target, scan_type, verbose)
    print(result)
