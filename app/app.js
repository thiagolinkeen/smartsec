const http = require('http');
const DOMPurify = require('dompurify');

http.createServer((req, res) => {
  const userInput = req.url.split('=')[1];
  
  // Sanitize user input before using it in the response
  const sanitizedInput = sanitizeUserInput(userInput);

  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(`<h1>Hello, ${sanitizedInput}</h1>`);
}).listen(3000, () => {
  console.log('Server running at http://localhost:3000/');
});

function sanitizeUserInput(input) {
  // Sanitize user input using DOMPurify to prevent XSS attacks
  return DOMPurify.sanitize(input);
}