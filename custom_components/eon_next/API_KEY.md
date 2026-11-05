# Creating an E.ON Next API key

1/ Log in to your account on www.eonnext.com
2/ open browser dashboard tab (F12): DevTools -> Console
(type `allow pasting` first). The script only creates a key if none exists.
The key is printed once. Store it in a password manager and never share it.
3/ Enter that ID into the Integration when adding it.

```js
(async () => {
  const url = 'https://api.eonnext-kraken.energy/v1/graphql/';
  const key = Object.keys(localStorage).find(x => x.startsWith('@@auth0spajs@@') && (() => { try { return !!JSON.parse(localStorage[x]).id_token } catch { return false } })());
  if (!key) return console.log('RESULT: no id_token entry');
  const t = JSON.parse(localStorage[key]).id_token;
  const gql = q => fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json', authorization: 'Bearer ' + t}, body: JSON.stringify({query: q})}).then(r => r.json());
  const c = await gql('query { viewer { liveSecretKey } }');
  if (c.errors || c.data.viewer.liveSecretKey) return console.log('RESULT: not creating', JSON.stringify(c.errors ?? c.data));
  const m = await gql('mutation { regenerateSecretKey { key } }');
  console.log('RESULT:', m.data?.regenerateSecretKey?.key ?? JSON.stringify(m.errors));
})();
```
