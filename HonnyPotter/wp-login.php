<?php
/**
 * WordPress Login Endpoint for HonnyPotter
 * 
 * This file mimics WordPress's wp-login.php endpoint.
 * Place this in your WordPress root directory (or symlink it).
 * 
 * It will capture all login attempts and forward them to HoneyBee.
 */

// Include HoneyBee forwarder
require_once __DIR__ . '/honeybee-forwarder.php';

// Get pot ID from environment or use default
$POT_ID = getenv('HONEYBEE_POT_ID') ?: 'honnypotter-01';

// Handle login POST
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['log']) && isset($_POST['pwd'])) {
    $username = trim($_POST['log']);
    $password = trim($_POST['pwd']);
    
    if (!empty($username) && !empty($password)) {
        // Forward to HoneyBee
        honeybee_forward_event($username, $password, null, null, $POT_ID);
    }
}

// Always return WordPress-style error
http_response_code(200);
header('Content-Type: text/html; charset=UTF-8');
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login &lsaquo; WordPress</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f0f1; }
        .error { background: #fff; border-left: 4px solid #dc3232; padding: 12px; margin: 20px 0; }
    </style>
</head>
<body>
    <div style="max-width: 400px; margin: 50px auto; padding: 20px; background: #fff;">
        <h1>WordPress</h1>
        <div class="error">
            <strong>ERROR</strong>: Invalid username or incorrect password.
        </div>
        <form method="post">
            <p>
                <label>Username or Email Address</label>
                <input type="text" name="log" style="width: 100%; padding: 8px;">
            </p>
            <p>
                <label>Password</label>
                <input type="password" name="pwd" style="width: 100%; padding: 8px;">
            </p>
            <p>
                <input type="submit" value="Log In" style="width: 100%; padding: 10px; background: #2271b1; color: #fff; border: none; cursor: pointer;">
            </p>
        </form>
    </div>
</body>
</html>

