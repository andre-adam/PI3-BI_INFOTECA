window.onload = ()=>{
    var interval = setInterval(()=>{
        if(!document.querySelector("#col1") && !document.querySelector("#col-graph-qtd-mes-por-area")){
            return;
        }
        function verificarWidth(){
            var width = window.innerWidth;
            if(width < 1200){
                document.querySelector("#col1").className = "col-md-12";
                document.querySelector("#col-graph-qtd-mes-por-area").className = "col-md-12";
                var evt = window.document.createEvent('UIEvents'); 
                evt.initUIEvent('resize', true, false, window, 0); 
                window.dispatchEvent(evt);
            }
        }
    
        verificarWidth();
        window.onresize = verificarWidth;
        clearInterval(interval);
    }, 100);
};