# SDK Investigation Quick Reference

**Date**: January 24, 2026  
**Status**: Investigation Complete ✅

---

## TL;DR

✅ **YES** - GitHub Copilot SDK enables autonomous agent triggering and multi-repo support.

**What's now possible**:
- Issue created → Webhook → SDK agent → PR created (no human required)
- GitHub App tokens authenticate SDK (bypasses user OAuth requirement)
- Single service can manage multiple repos
- Minimal per-repo setup (one config file)

**Cost**: $50-230/month depending on scale  
**Timeline**: 2 weeks for prototype, 6-10 weeks for production multi-repo

---

## Key Documents

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [SDK Investigation](./sdk-investigation.md) | Complete analysis with evidence | 30 min |
| [Architecture Proposal](./sdk-architecture-proposal.md) | Detailed technical design | 20 min |
| [Setup Guide](./sdk-setup-guide.md) | Step-by-step implementation | 15 min |
| [Automation Limits (Updated)](./automation-limits.md) | Context and comparison | 10 min |

---

## Answer to Core Questions

### 1. Can SDK enable autonomous triggering?

**✅ YES**

- SDK provides programmatic access to Copilot agents
- Webhook → Service → SDK → PR workflow fully supported
- No human intervention required after issue is labeled
- Evidence: GitHub blog post, SDK repository, web search results

### 2. Can GitHub App tokens authenticate SDK?

**✅ YES**

- SDK accepts `COPILOT_GITHUB_TOKEN` environment variable
- GitHub App installation tokens work with this variable
- Bypasses previous user OAuth requirement
- Tokens auto-renewable (1 hour expiry, code handles refresh)

### 3. Can external service + SDK replace per-repo setup?

**✅ YES**

- Single service monitors multiple repos via webhooks
- Per-repo config: just `kerrigan.json` (minimal)
- No workflow files needed in target repos
- Central prompt management
- Central dashboard for all repos

### 4. What's the cost?

**$50-230/month** depending on:
- Number of repos
- Issues per month
- SDK requests per issue (20-50 typical)

**Breakdown**:
- Copilot Pro+: $39/month (1,500 requests)
- Infrastructure: $10-35/month (Railway/Render)
- Database (optional): $5/month
- Monitoring: $0-10/month

---

## Recommended Architecture

### For Kerrigan Repository (Single Repo)

**Hybrid Approach**:
- Keep existing GitHub Actions (CI, validation, gates)
- Add SDK service for autonomous triggering
- Gradually migrate based on proven value

**Benefits**:
- Non-disruptive addition
- Can test before full commitment
- Preserves existing automation

### For Multi-Repo Adoption

**Central Service Pattern**:
- One service for organization
- GitHub App installed on all repos
- Each repo has `kerrigan.json` (50 lines)
- No workflow files in repos

**Benefits**:
- 2-minute setup per new repo
- No workflow conflicts
- Central management
- Better for scaling

---

## Implementation Phases

### Phase 1: Prototype (2 weeks)
- Create basic Node.js service
- Integrate Copilot SDK
- Test with 1-2 issues
- Validate cost model

### Phase 2: Kerrigan Integration (2 weeks)
- Deploy to Railway
- Configure webhooks
- Test with real issues
- Monitor for 1-2 weeks

### Phase 3: Hardening (2 weeks)
- Add error handling
- Implement monitoring
- Security audit
- Performance optimization

### Phase 4: Multi-Repo (4 weeks)
- Implement config manager
- Build dashboard
- Pilot with 2-3 repos
- Gather feedback

### Phase 5: Public Release (ongoing)
- Open-source service
- Documentation polish
- Community building

**Total**: ~10 weeks to production multi-repo

---

## Quick Decision Matrix

### Should you use SDK approach?

**Use SDK if**:
- ✅ Want fully autonomous triggering (no @-mentions)
- ✅ Managing multiple repos
- ✅ Can host external service
- ✅ Budget allows $50-230/month

**Stick with Actions if**:
- ✅ Single repo only
- ✅ Semi-manual triggering acceptable
- ✅ Don't want external hosting
- ✅ No budget for Copilot Pro+

**Hybrid approach if**:
- ✅ Want to test SDK capabilities
- ✅ Keep existing automation working
- ✅ Gradual migration preferred
- ✅ Risk-averse

---

## Code Example (Minimal)

```javascript
// Autonomous agent triggering in ~50 lines
import { CopilotClient } from '@github/copilot-sdk';
import express from 'express';

const app = express();
const sdk = new CopilotClient();
await sdk.start();

app.post('/webhook', async (req, res) => {
  const { action, issue, label } = req.body;
  
  if (action === 'labeled' && label?.name === 'agent:go') {
    // Trigger agent asynchronously
    const session = await sdk.createSession({
      model: 'gpt-5',
      context: { issue: issue.number }
    });
    
    await session.send({
      prompt: `Create PR for: ${issue.title}\n${issue.body}`
    });
    
    return res.status(202).send('Agent triggered');
  }
  
  res.status(200).send('OK');
});

app.listen(3000);
```

---

## Security Checklist

Before production:
- [ ] Webhook signature verification
- [ ] Private key in secure vault (not code)
- [ ] Rate limiting implemented
- [ ] Input validation on webhooks
- [ ] Error messages don't leak secrets
- [ ] HTTPS only
- [ ] Dependency updates automated
- [ ] Security scanning enabled

---

## Cost Optimization Tips

1. **Filter early** - Only process specific labels
2. **Cache context** - Store repo context for reuse
3. **Batch requests** - Process related issues together
4. **Monitor closely** - Alert before hitting limits
5. **Right-size plan** - Start small, scale as needed

---

## Common Pitfalls

❌ **Don't**: Hard-code credentials  
✅ **Do**: Use environment variables and vaults

❌ **Don't**: Skip webhook signature verification  
✅ **Do**: Verify every webhook

❌ **Don't**: Ignore rate limits  
✅ **Do**: Implement queuing and limits

❌ **Don't**: Run SDK in GitHub Actions  
✅ **Do**: Use external service

❌ **Don't**: Over-engineer initially  
✅ **Do**: Start simple, iterate

---

## Next Steps

### Immediate (This Week)
1. Review investigation documents
2. Decide on architecture (hybrid vs. centralized)
3. Approve budget (~$50-100/month to start)

### Short-term (Next 2-4 Weeks)
1. Create GitHub App
2. Build prototype service
3. Deploy to Railway
4. Test with 5-10 issues

### Medium-term (2-3 Months)
1. Validate cost model
2. Harden for production
3. Document learnings
4. Plan multi-repo expansion

### Long-term (3-6 Months)
1. Scale to multiple repos
2. Build dashboard
3. Open-source service
4. Community building

---

## Support Resources

- **Investigation Report**: [docs/sdk-investigation.md](./sdk-investigation.md)
- **Architecture**: [docs/sdk-architecture-proposal.md](./sdk-architecture-proposal.md)
- **Setup Guide**: [docs/sdk-setup-guide.md](./sdk-setup-guide.md)
- **GitHub Copilot SDK**: https://github.com/github/copilot-sdk
- **GitHub Apps Guide**: https://docs.github.com/en/apps

---

## Success Metrics

Track these to validate value:

**Efficiency**:
- Time from issue to PR (target: <5 minutes)
- Issues processed per week
- Human intervention rate (target: <10%)

**Quality**:
- PR approval rate (target: >80%)
- Tests passing on first attempt (target: >90%)
- Code review iterations (target: <2)

**Cost**:
- Cost per issue (target: <$1)
- SDK requests per issue (target: <40)
- Monthly total cost vs. budget

**Adoption** (multi-repo):
- Repos onboarded
- Setup time per repo (target: <5 minutes)
- User satisfaction (surveys)

---

## FAQ

**Q: Does this replace GitHub Actions?**  
A: No. Actions still handle CI, validation, and gates. SDK adds autonomous triggering.

**Q: Can I use this with private repos?**  
A: Yes. GitHub App can be installed on private repos.

**Q: What if SDK API changes?**  
A: Monitor SDK releases, maintain version compatibility, test before upgrading.

**Q: Is this officially supported by GitHub?**  
A: Yes. SDK is official GitHub product (technical preview as of Jan 2026).

**Q: Can I self-host instead of using Railway?**  
A: Yes. Any Node.js hosting works. Railway is just convenient.

**Q: What about costs for large organizations?**  
A: Enterprise plan ($39/seat) provides 1,000 requests/seat/month. 5 seats = 5,000/month.

**Q: Can agents work on multiple issues simultaneously?**  
A: Yes. SDK supports multiple concurrent sessions.

**Q: How do I roll back if something goes wrong?**  
A: Pause webhook, fix service, test, resume. Existing automation remains unaffected.

---

**Last Updated**: January 24, 2026  
**Version**: 1.0  
**Status**: Investigation Complete ✅
