# NaturalDocs

<div class="iframe-container">
    <iframe 
        sandbox="allow-forms allow-scripts allow-same-origin" 
        src="../ndocs/index.html" 
        width="100%" 
        height="600px"></iframe>
</div>

<style>
    .iframe-container {
        position: relative;
        width: 100%;
        height: 80vh; /* Sets height to 80% of the screen */
        overflow: hidden;
    }
    .iframe-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
    }
</style>

<script>
  const myIframe = document.querySelector('iframe');
  myIframe.addEventListener('load', function() {
    // This finds every link inside the iframe and forces it to stay inside
    const links = myIframe.contentWindow.document.getElementsByTagName('a');
    for (let i = 0; i < links.length; i++) {
      links[i].setAttribute('target', '_self');
    }
  });
</script>