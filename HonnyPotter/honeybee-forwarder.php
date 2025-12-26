<?php
/**
 * HoneyBee Event Forwarder for HonnyPotter
 * 
 * Sends WordPress login honeypot events to HoneyBee Node via TCP socket.
 * Protocol: JSON over TCP to localhost:9100
 * 
 * Usage: Include this file in your HonnyPotter installation and call
 * honeybee_forward_event() whenever a failed login is detected.
 */

/**
 * Forward a failed login event to HoneyBee Node
 * 
 * @param string $username Username attempted
 * @param string $password Password attempted
 * @param string $ip_address Source IP address
 * @param string $user_agent User agent string
 * @param string $pot_id Honeypot instance ID
 * @return bool True if event was sent successfully, false otherwise
 */
function honeybee_forward_event($username, $password, $ip_address = null, $user_agent = null, $pot_id = 'honnypotter-01')
{
    // Get source IP if not provided
    if ($ip_address === null) {
        $ip_address = honeybee_get_client_ip();
    }
    
    // Get user agent if not provided
    if ($user_agent === null) {
        $user_agent = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : 'Unknown';
    }
    
    // Build event payload
    $event = [
        'eventid' => 'honnypotter.login.failed',
        'pot_id' => $pot_id,
        'pot_type' => 'honnypotter',
        'timestamp' => time(),
        'src_ip' => $ip_address,
        'src_port' => isset($_SERVER['REMOTE_PORT']) ? (int)$_SERVER['REMOTE_PORT'] : 0,
        'dst_port' => isset($_SERVER['SERVER_PORT']) ? (int)$_SERVER['SERVER_PORT'] : 80,
        'username' => $username,
        'password' => $password,
        'user_agent' => $user_agent,
        'request_uri' => isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '/',
        'request_method' => isset($_SERVER['REQUEST_METHOD']) ? $_SERVER['REQUEST_METHOD'] : 'POST',
        'message' => sprintf('Failed login attempt: %s from %s', $username, $ip_address),
        'honeybee_category' => 'authentication',
        'honeybee_severity' => 'medium'
    ];
    
    // Send to HoneyBee Node
    return honeybee_send_event($event);
}

/**
 * Send event to HoneyBee Node via TCP socket
 * 
 * @param array $event Event data
 * @return bool True if sent successfully
 */
function honeybee_send_event($event)
{
    $host = '127.0.0.1';
    $port = 9100;
    $timeout = 5;
    
    // Create socket connection
    $socket = @socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
    if ($socket === false) {
        error_log('HoneyBee: Failed to create socket');
        return false;
    }
    
    // Set timeout
    @socket_set_option($socket, SOL_SOCKET, SO_SNDTIMEO, ['sec' => $timeout, 'usec' => 0]);
    
    // Connect to HoneyBee Node
    $connected = @socket_connect($socket, $host, $port);
    if ($connected === false) {
        error_log('HoneyBee: Failed to connect to ' . $host . ':' . $port);
        @socket_close($socket);
        return false;
    }
    
    // Encode event as JSON
    $json = json_encode($event) . "\n";
    
    // Send event
    $sent = @socket_write($socket, $json, strlen($json));
    if ($sent === false) {
        error_log('HoneyBee: Failed to send event');
        @socket_close($socket);
        return false;
    }
    
    // Close socket
    @socket_close($socket);
    
    return true;
}

/**
 * Get client IP address
 * 
 * @return string IP address
 */
function honeybee_get_client_ip()
{
    $ip_keys = [
        'HTTP_CF_CONNECTING_IP', // Cloudflare
        'HTTP_X_REAL_IP',        // Nginx proxy
        'HTTP_X_FORWARDED_FOR',  // Proxy
        'REMOTE_ADDR'            // Direct connection
    ];
    
    foreach ($ip_keys as $key) {
        if (!empty($_SERVER[$key])) {
            $ip = $_SERVER[$key];
            
            // Handle comma-separated IPs (X-Forwarded-For)
            if (strpos($ip, ',') !== false) {
                $ips = explode(',', $ip);
                $ip = trim($ips[0]);
            }
            
            // Validate IP
            if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
                return $ip;
            }
        }
    }
    
    // Fallback to REMOTE_ADDR
    return isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '0.0.0.0';
}

/**
 * Forward XML-RPC authentication failure
 * 
 * @param string $username Username attempted
 * @param string $password Password attempted
 * @param string $pot_id Honeypot instance ID
 * @return bool True if sent successfully
 */
function honeybee_forward_xmlrpc_failed($username, $password, $pot_id = 'honnypotter-01')
{
    $event = [
        'eventid' => 'honnypotter.xmlrpc.failed',
        'pot_id' => $pot_id,
        'pot_type' => 'honnypotter',
        'timestamp' => time(),
        'src_ip' => honeybee_get_client_ip(),
        'src_port' => isset($_SERVER['REMOTE_PORT']) ? (int)$_SERVER['REMOTE_PORT'] : 0,
        'dst_port' => isset($_SERVER['SERVER_PORT']) ? (int)$_SERVER['SERVER_PORT'] : 80,
        'username' => $username,
        'password' => $password,
        'user_agent' => isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : 'Unknown',
        'request_uri' => isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '/xmlrpc.php',
        'request_method' => isset($_SERVER['REQUEST_METHOD']) ? $_SERVER['REQUEST_METHOD'] : 'POST',
        'message' => sprintf('XML-RPC authentication failed: %s', $username),
        'honeybee_category' => 'authentication',
        'honeybee_severity' => 'medium'
    ];
    
    return honeybee_send_event($event);
}

