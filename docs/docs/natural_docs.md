# NaturalDocs

I have documented my code using ![NaturalDocs](https://naturaldocs.org). I have found it excellent for readability and not super cumbersome to use, with little repetition. The unfortunate downside is that it's not very nice to include in other sites, so I've had to go with a somewhat clunky `iframe` approach. I've also had to disable linking, since that would entirely override the page.

That said, it's mainly used for documentation while working with the code, not for use in a documentation website. However, I thought it would be interesting to include, since I already had it.

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