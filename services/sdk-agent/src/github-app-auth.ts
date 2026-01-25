/**
 * GitHub App Authentication
 * Manages GitHub App installation tokens for SDK authentication
 */

import { createAppAuth } from '@octokit/auth-app';
import { Octokit } from '@octokit/rest';

export class GitHubAppAuth {
  private appId: string;
  private privateKey: string;
  private installationId?: number;
  private cachedToken?: {
    token: string;
    expiresAt: Date;
  };

  constructor(appId: string, privateKey: string) {
    this.appId = appId;
    this.privateKey = privateKey;
  }

  /**
   * Get installation token for the repository
   * Caches token and refreshes before expiry
   */
  async getInstallationToken(owner: string, repo: string): Promise<string> {
    // Check if cached token is still valid (refresh 5 minutes before expiry)
    if (this.cachedToken) {
      const now = new Date();
      const expiryBuffer = new Date(this.cachedToken.expiresAt.getTime() - 5 * 60 * 1000);
      if (now < expiryBuffer) {
        console.log('✅ Using cached GitHub App installation token');
        return this.cachedToken.token;
      }
    }

    console.log('🔄 Fetching new GitHub App installation token...');

    // Create App authentication
    const auth = createAppAuth({
      appId: this.appId,
      privateKey: this.privateKey,
    });

    // Get installation ID for this repository
    if (!this.installationId) {
      const appOctokit = new Octokit({
        authStrategy: createAppAuth,
        auth: {
          appId: this.appId,
          privateKey: this.privateKey,
        },
      });

      const { data: installation } = await appOctokit.apps.getRepoInstallation({
        owner,
        repo,
      });

      this.installationId = installation.id;
      console.log(`📍 Found installation ID: ${this.installationId}`);
    }

    // Get installation token
    const { token, expiresAt } = await auth({
      type: 'installation',
      installationId: this.installationId,
    });

    // Cache token
    this.cachedToken = {
      token,
      expiresAt: new Date(expiresAt),
    };

    console.log(`✅ New token obtained, expires at: ${expiresAt}`);
    return token;
  }

  /**
   * Create authenticated Octokit client
   */
  async createOctokitClient(owner: string, repo: string): Promise<Octokit> {
    const token = await this.getInstallationToken(owner, repo);
    return new Octokit({ auth: token });
  }

  /**
   * Validate GitHub App credentials
   */
  async validate(): Promise<boolean> {
    try {
      const auth = createAppAuth({
        appId: this.appId,
        privateKey: this.privateKey,
      });

      await auth({ type: 'app' });
      console.log('✅ GitHub App credentials valid');
      return true;
    } catch (error) {
      console.error('❌ GitHub App credentials invalid:', error);
      return false;
    }
  }
}
