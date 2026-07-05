<?php
/**
 * ATELIER — iletişim formu işleyici (turkticaret.net PHP hosting)
 * public/contact.php → build'de dist/contact.php olarak yayınlanır.
 *
 * KURULUM: Aşağıdaki $TO adresini gerçek alıcı e-postasıyla değiştir.
 */

$TO = 'bora@pusnco.com'; // <-- GERÇEK ALICI ADRESİ

// Dil ve geri dönüş yolu
$lang = preg_replace('/[^a-z]/', '', $_POST['lang'] ?? 'en');
if ($lang !== 'tr') { $lang = 'en'; }
$back = '/' . $lang . '/contact';

// Sadece POST kabul et
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header("Location: $back");
    exit;
}

// Honeypot — bot doldurduysa sessizce başarı gibi davran
if (!empty($_POST['company'])) {
    header("Location: $back?sent=1");
    exit;
}

$name    = trim($_POST['name'] ?? '');
$email   = trim($_POST['email'] ?? '');
$message = trim($_POST['message'] ?? '');

// Doğrulama
if ($name === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || $message === '') {
    header("Location: $back?error=1");
    exit;
}

// Enjeksiyona karşı başlık temizliği
$name  = str_replace(["\r", "\n"], ' ', $name);
$email = str_replace(["\r", "\n"], ' ', $email);

$host    = $_SERVER['HTTP_HOST'] ?? 'localhost';
$subject = 'Yeni iletişim formu — ' . $name;
$body    = "Ad: $name\nE-posta: $email\n\nMesaj:\n$message\n";

$headers  = "From: website@$host\r\n";
$headers .= "Reply-To: $email\r\n";
$headers .= "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

$encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';

@mail($TO, $encodedSubject, $body, $headers);

header("Location: $back?sent=1");
exit;
