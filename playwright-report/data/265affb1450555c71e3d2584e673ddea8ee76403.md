# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]: "[plugin:vite-plugin-svelte] /home/samuel/projects/escala/src/routes/members/+page.svelte:238:23 Expected a valid element or component name. Components must have a valid variable name or dot notation expression https://svelte.dev/e/tag_invalid_name"
  - generic [ref=e6]: /home/samuel/projects/escala/src/routes/members/+page.svelte:238:23
  - generic [ref=e7]: 236 | 237 | 238 | let members = $state<Member[]>([]); ^ 239 | let loading = $state(true); 240 | let search = $state('');
  - generic [ref=e8]:
    - text: Click outside, press Esc key, or fix the code to dismiss.
    - text: You can also disable this overlay by setting
    - code [ref=e9]: server.hmr.overlay
    - text: to
    - code [ref=e10]: "false"
    - text: in
    - code [ref=e11]: vite.config.js
    - text: .
```