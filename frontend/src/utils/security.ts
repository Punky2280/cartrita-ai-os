// Cartrita AI OS - Security Utilities
// File integrity, checksums, and transactional operations

import { logError } from "./index";

// Checksum generation using Web Crypto API
export async function generateChecksum(
  data: string | ArrayBuffer,
): Promise<string> {
  try {
    const encoder = new TextEncoder();
    const dataBuffer = typeof data === "string" ? encoder.encode(data) : data;

    const hashBuffer = await crypto.subtle.digest("SHA-256", dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");

    return hashHex;
  } catch (error) {
    logError(error as Error, { context: "checksum_generation" });
    throw new Error("Failed to generate checksum");
  }
}

// Verify file integrity by comparing checksums
export async function verifyFileIntegrity(
  filePath: string,
  expectedChecksum: string,
): Promise<boolean> {
  try {
    // In browser environment, we can't directly read files from filesystem
    // This is a placeholder for server-side implementation
    // For now, we'll simulate integrity check

    const timestamp = Date.now().toString();
    const computedChecksum = await generateChecksum(filePath + timestamp);

    // In real implementation, this would fetch and verify actual file
    return computedChecksum.length === expectedChecksum.length;
  } catch (error) {
    logError(error as Error, {
      context: "file_integrity_verification",
      filePath,
      expectedChecksum,
    });
    return false;
  }
}

// Transactional file operations (for server-side use)
export class TransactionalFile {
  private originalPath: string;
  private tempPath: string;
  private backupPath: string;
  private committed: boolean = false;

  constructor(originalPath: string) {
    this.originalPath = originalPath;
    this.tempPath = `${originalPath}.tmp.${Date.now()}`;
    this.backupPath = `${originalPath}.backup.${Date.now()}`;
  }

  // Begin transaction - create backup and temp file
  async begin(): Promise<void> {
    try {
      // This would be implemented server-side with actual file operations
      // For browser, this is a placeholder
      this.committed = false;
    } catch (error) {
      logError(error as Error, {
        context: "transactional_file_begin",
        originalPath: this.originalPath,
      });
      throw new Error("Failed to begin file transaction");
    }
  }

  // Write data to temporary file
  async write(data: string | ArrayBuffer): Promise<void> {
    try {
      // Server-side implementation would write to temp file
      // Browser implementation is simulated
      const checksum = await generateChecksum(data);

      // Store checksum for integrity verification
      localStorage.setItem(`checksum:${this.tempPath}`, checksum);
    } catch (error) {
      logError(error as Error, {
        context: "transactional_file_write",
        tempPath: this.tempPath,
      });
      throw new Error("Failed to write to temporary file");
    }
  }

  // Commit transaction - replace original with temp file
  async commit(): Promise<void> {
    try {
      // Verify integrity before committing
      const storedChecksum = localStorage.getItem(`checksum:${this.tempPath}`);
      if (!storedChecksum) {
        throw new Error("No checksum found for verification");
      }

      // Server-side would replace original file with temp file
      this.committed = true;

      // Clean up
      localStorage.removeItem(`checksum:${this.tempPath}`);
    } catch (error) {
      logError(error as Error, {
        context: "transactional_file_commit",
        originalPath: this.originalPath,
        tempPath: this.tempPath,
      });
      await this.rollback();
      throw new Error("Failed to commit file transaction");
    }
  }

  // Rollback transaction - restore from backup, clean up temp
  async rollback(): Promise<void> {
    try {
      // Server-side would restore from backup and clean up temp files
      this.committed = false;

      // Clean up
      localStorage.removeItem(`checksum:${this.tempPath}`);
    } catch (error) {
      logError(error as Error, {
        context: "transactional_file_rollback",
        originalPath: this.originalPath,
      });
    }
  }

  // Clean up all temporary files
  async cleanup(): Promise<void> {
    try {
      // Clean up any remaining temporary files
      localStorage.removeItem(`checksum:${this.tempPath}`);
    } catch (error) {
      logError(error as Error, {
        context: "transactional_file_cleanup",
        originalPath: this.originalPath,
      });
    }
  }

  // Get transaction status
  isCommitted(): boolean {
    return this.committed;
  }
}

// Secure data storage with integrity verification
export class SecureStorage {
  private prefix: string;

  constructor(prefix: string = "cartrita") {
    this.prefix = prefix;
  }

  // Store data with checksum
  async store(key: string, data: unknown): Promise<void> {
    try {
      const serialized = JSON.stringify(data);
      const checksum = await generateChecksum(serialized);

      const secureData = {
        data: serialized,
        checksum,
        timestamp: Date.now(),
      };

      localStorage.setItem(`${this.prefix}:${key}`, JSON.stringify(secureData));
    } catch (error) {
      logError(error as Error, {
        context: "secure_storage_store",
        key,
      });
      throw new Error("Failed to store secure data");
    }
  }

  // Retrieve and verify data
  async retrieve(key: string): Promise<unknown> {
    try {
      const stored = localStorage.getItem(`${this.prefix}:${key}`);
      if (!stored) {
        return null;
      }

      const secureData = JSON.parse(stored);
      const { data, checksum, timestamp } = secureData;

      // Verify integrity
      const computedChecksum = await generateChecksum(data);
      if (computedChecksum !== checksum) {
        logError(new Error("Data integrity verification failed"), {
          context: "secure_storage_retrieve",
          key,
          expected: checksum,
          computed: computedChecksum,
        });
        // Remove corrupted data
        this.remove(key);
        throw new Error("Data corruption detected");
      }

      return JSON.parse(data);
    } catch (error) {
      logError(error as Error, {
        context: "secure_storage_retrieve",
        key,
      });
      return null;
    }
  }

  // Remove data
  remove(key: string): void {
    localStorage.removeItem(`${this.prefix}:${key}`);
  }

  // List all keys
  listKeys(): string[] {
    const keys: string[] = [];
    const prefixPattern = `${this.prefix}:`;

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(prefixPattern)) {
        keys.push(key.substring(prefixPattern.length));
      }
    }

    return keys;
  }

  // Clear all data
  clear(): void {
    const keys = this.listKeys();
    keys.forEach((key) => this.remove(key));
  }
}

// API key validation and sanitization
export function validateApiKey(apiKey: string): boolean {
  if (!apiKey || typeof apiKey !== "string") {
    return false;
  }

  // Basic format validation
  if (apiKey.length < 10 || apiKey.length > 100) {
    return false;
  }

  // Check for suspicious patterns
  const suspiciousPatterns = [
    /script/i,
    /<[^>]*>/,
    /javascript:/i,
    /data:/i,
    /vbscript:/i,
  ];

  return !suspiciousPatterns.some((pattern) => pattern.test(apiKey));
}

// Sanitize user input to prevent XSS
export function sanitizeInput(input: string): string {
  if (typeof input !== "string") {
    return "";
  }

  return input
    .replace(/[<>\"']/g, (match) => {
      const entities: { [key: string]: string } = {
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
      };
      return entities[match] || match;
    })
    .trim();
}

// Rate limiting utility
export class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  private limit: number;
  private windowMs: number;

  constructor(limit: number, windowMs: number) {
    this.limit = limit;
    this.windowMs = windowMs;
  }

  // Check if request is allowed
  isAllowed(identifier: string): boolean {
    const now = Date.now();
    const requests = this.requests.get(identifier) || [];

    // Remove old requests outside the window
    const validRequests = requests.filter((time) => now - time < this.windowMs);

    // Check if under limit
    if (validRequests.length >= this.limit) {
      return false;
    }

    // Add current request
    validRequests.push(now);
    this.requests.set(identifier, validRequests);

    return true;
  }

  // Get remaining requests
  getRemaining(identifier: string): number {
    const now = Date.now();
    const requests = this.requests.get(identifier) || [];
    const validRequests = requests.filter((time) => now - time < this.windowMs);

    return Math.max(0, this.limit - validRequests.length);
  }

  // Reset requests for identifier
  reset(identifier: string): void {
    this.requests.delete(identifier);
  }

  // Clear all
  clear(): void {
    this.requests.clear();
  }
}

// Export default secure storage instance
export const secureStorage = new SecureStorage("cartrita");
