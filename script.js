const btn = document.getElementById("btn")


btn.addEventListener("click",async ()=>{
    const t = document.getElementById("time")
    let period = t.value;

    let cards = document.getElementById("cards")

    cards.innerHTML = ""

    await fetch('http://35.160.120.126:8000/period',{
        method : "POST",
        headers : {
            'Content-Type': 'application/json',  
        },
        body : JSON.stringify({time : period})
    })

    const ws = new WebSocket("ws://35.160.120.126:8000/ws")       
    ws.onmessage = (event)=>{
        let  data = JSON.parse(event.data)
        
        let length = data["place"].length;
        

    
        for(let i=0; i<length;i++){
            cards.innerHTML = cards.innerHTML + 
               `<div class="card">
                <h2>${data['place'][i]}</h2>
                <p><strong>Magnitude:</strong> <span class="magnitude">${data['magnitude'][i]} ${data['magType'][i]}</span></p>
                <p><strong>Details:</strong> ${data['title'][i]}</p>
                <p><strong>Type:</strong> ${data['type'][i]}</p>
                <p><strong>Coordinates:</strong> ${data['coordinates'][i]}</p>
                <p><strong>Tsunami:</strong> <span class="tsunami">${data['tsunami'][i]}</span></p>
                <p><strong>Predictions:</strong> <span class="risk ${data['predictions'][i]}">${data['predictions'][i]} Risk</span></p>
                <p><strong>url:</strong> <span ><a href =${data['url'][i]} target="_blank" >click here</a></span></p>
                <p><strong>Details:</strong> <span ><a href =${data['details'][i]} target="_blank" >click here</a></span></p>
            </div>`
         
        }

}
})


