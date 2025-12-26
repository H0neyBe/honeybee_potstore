<?php
/**
 * HonnyPotter Standalone - WordPress Login Honeypot
 * 
 * Standalone version of HonnyPotter that works without WordPress.
 * Captures failed login attempts and forwards them to HoneyBee Node.
 * 
 * Installation:
 * 1. Place this file in a web-accessible directory
 * 2. Configure $POT_ID and other settings below
 * 3. Point WordPress login form action to this file, or use as standalone endpoint
 * 
 * Usage:
 * - POST to this file with 'log' and 'pwd' parameters (WordPress login form)
 * - Or use as XML-RPC endpoint: POST to /xmlrpc.php (if configured)
 */

// Include HoneyBee forwarder
require_once __DIR__ . '/honeybee-forwarder.php';

// Configuration
$POT_ID = getenv('HONEYBEE_POT_ID') ?: 'honnypotter-01';
$LOG_FILE = getenv('HONEYBEE_LOG_FILE') ?: __DIR__ . '/honnypotter.log';
$ENABLE_FILE_LOG = getenv('HONEYBEE_ENABLE_FILE_LOG') !== 'false';
$ENABLE_HONEYBEE = getenv('HONEYBEE_ENABLE') !== 'false';

// WordPress login endpoint simulation
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = isset($_POST['log']) ? trim($_POST['log']) : '';
    $password = isset($_POST['pwd']) ? trim($_POST['pwd']) : '';
    
    // Also check for XML-RPC format
    if (empty($username) && isset($_POST['username'])) {
        $username = trim($_POST['username']);
    }
    if (empty($password) && isset($_POST['password'])) {
        $password = trim($_POST['password']);
    }
    
    // Check if this is an XML-RPC request
    $is_xmlrpc = (
        strpos($_SERVER['REQUEST_URI'] ?? '', 'xmlrpc') !== false ||
        isset($_POST['xmlrpc']) ||
        (isset($_SERVER['CONTENT_TYPE']) && strpos($_SERVER['CONTENT_TYPE'], 'text/xml') !== false)
    );
    
    // Only log failed attempts (we always fail - it's a honeypot!)
    if (!empty($username) && !empty($password)) {
        $ip_address = honeybee_get_client_ip();
        $user_agent = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : 'Unknown';
        
        // Log to file if enabled
        if ($ENABLE_FILE_LOG) {
            $log_entry = sprintf(
                "%s - %s:%s [%s] %s\n",
                date('Y-m-d H:i:s'),
                $username,
                $password,
                $ip_address,
                $user_agent
            );
            @file_put_contents($LOG_FILE, $log_entry, FILE_APPEND | LOCK_EX);
        }
        
        // Forward to HoneyBee Node
        if ($ENABLE_HONEYBEE) {
            if ($is_xmlrpc) {
                honeybee_forward_xmlrpc_failed($username, $password, $POT_ID);
            } else {
                honeybee_forward_event($username, $password, $ip_address, $user_agent, $POT_ID);
            }
        }
        
        // Return WordPress-style error (always fail)
        http_response_code(200);
        header('Content-Type: text/html; charset=UTF-8');
        echo '<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login &lsaquo; WordPress</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .error { background: #fff; border-left: 4px solid #dc3232; padding: 12px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="error">
        <strong>ERROR</strong>: Invalid username or incorrect password.
    </div>
</body>
</html>';
        exit;
    }
}

// Default: Show login form or return 200 OK
http_response_code(200);
header('Content-Type: text/html; charset=UTF-8');
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login &lsaquo; WordPress</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f0f0f1;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .login {
            background: #fff;
            padding: 30px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            width: 320px;
        }
        h1 {
            font-size: 24px;
            margin: 0 0 20px 0;
            text-align: center;
        }
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        input[type="submit"] {
            width: 100%;
            padding: 10px;
            background: #2271b1;
            color: #fff;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        input[type="submit"]:hover {
            background: #135e96;
        }
    </style>
</head>
<body>
    <div class="login">
        <h1>WordPress</h1>
        <form method="post" action="">
            <p>
                <label for="log">Username or Email Address</label>
                <input type="text" name="log" id="log" required>
            </p>
            <p>
                <label for="pwd">Password</label>
                <input type="password" name="pwd" id="pwd" required>
            </p>
            <p>
                <input type="submit" value="Log In">
            </p>
        </form>
    </div>
</body>
</html>

