window.onload = ()=>{
    function verificar(){
        if(!document.querySelector("#col1") && !document.querySelector("#col-graph-qtd-mes-por-area")){
            return;
        }
        var width = window.innerWidth;
        if(width < 1200){
            document.querySelector("#col1").className = "col-md-12";
            document.querySelector("#col-graph-qtd-mes-por-area").className = "col-md-12";
        } else {
            document.querySelector("#col1").className = "col-md-5";
            document.querySelector("#col-graph-qtd-mes-por-area").className = "col-md-7";
        };
    };
    window.onresize = verificar;
    // var interval = setInterval(()=>{
    //     verificar();
    // },1000);
    var check = setInterval(()=>{
        if(!document.querySelector("#col1") && !document.querySelector("#col-graph-qtd-mes-por-area")){
            return;
        } else {
            var evt = window.document.createEvent('UIEvents'); 
            evt.initUIEvent('resize', true, false, window, 0); 
            window.dispatchEvent(evt);
            clearInterval(check);
        }
    })
};