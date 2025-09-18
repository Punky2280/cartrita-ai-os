/* eslint-env node */

// Check if a domain is in our allowed list
function isAllowedDomain(uri) {
  const allowedDomains = [
    'fonts.googleapis.com',
    'fonts.gstatic.com',
    'api.openai.com',
    'api.deepgram.com',
    process.env.FRONTEND_URL,
    process.env.NEXT_PUBLIC_API_URL
  ].filter(Boolean);

  return allowedDomains.some(domain => uri.includes(domain));
}

// Analyze the severity of a CSP violation
function analyzeSeverity(report) {
  const violatedDirective = report['violated-directive'] || '';
  const blockedUri = report['blocked-uri'] || '';

  // Critical: Script injection attempts (potential XSS)
  if (violatedDirective.includes('script-src') &&
      (blockedUri.includes('javascript') ||
       blockedUri.includes('data:') ||
       blockedUri.includes('blob:'))) {
    return 'critical';
  }

  // High: External script/style loading from unexpected domains
  if ((violatedDirective.includes('script-src') || violatedDirective.includes('style-src')) &&
      blockedUri.startsWith('http') &&
      !isAllowedDomain(blockedUri)) {
    return 'high';
  }

  // Medium: Other directive violations
  if (violatedDirective.includes('connect-src') ||
      violatedDirective.includes('img-src') ||
      violatedDirective.includes('frame-src')) {
    return 'medium';
  }

  // Low: Minor violations
  return 'low';
}

// CSP Violation reporting endpoint for API Gateway
async function cspViolationHandler(request, reply) {
  try {
    const violation = request.body;

    // Basic validation of CSP violation report
    if (!violation || !violation['csp-report']) {
      reply.code(400).send({ error: 'Invalid CSP violation report format' });
      return;
    }

    const report = violation['csp-report'];

    // Log the violation (in production, send to monitoring system)
    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'csp_violation',
      blockedUri: report['blocked-uri'],
      documentUri: report['document-uri'],
      violatedDirective: report['violated-directive'],
      originalPolicy: report['original-policy'],
      sourceFile: report['source-file'],
      lineNumber: report['line-number'],
      columnNumber: report['column-number'],
      userAgent: request.headers['user-agent'],
      ipAddress: request.ip
    };

    // Determine violation severity
    const severity = analyzeSeverity(report);
    logEntry.severity = severity;

    // Log based on severity
    if (severity === 'critical') {
      console.error('CRITICAL CSP VIOLATION:', JSON.stringify(logEntry, null, 2));
    } else if (severity === 'high') {
      console.warn('HIGH CSP VIOLATION:', JSON.stringify(logEntry, null, 2));
    } else {
      console.info('CSP VIOLATION:', JSON.stringify(logEntry, null, 2));
    }

    // In production, you might want to:
    // - Send to security monitoring system
    // - Store in database for analysis
    // - Trigger alerts for critical violations

    reply.code(204).send(); // No content response
  } catch (error) {
    console.error('Error processing CSP violation report:', error);
    reply.code(500).send({ error: 'Internal server error' });
  }
}

module.exports = {
  cspViolationHandler
};
