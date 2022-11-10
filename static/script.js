//particle background creation
const particles = [];
function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

function setup() {
    createCanvas(window.outerWidth, window.outerHeight);
    canvas.id = "particles"
    const particlesLength = Math.floor(window.innerWidth / 10);

    for(let i = 0; i < particlesLength; i++) {
        particles.push(new Particle());
    }
}

function draw() {
    background(47,48,56);
    particles.forEach((p, index) => {
        p.update();
        p.draw();
        p.checkParticles(particles.slice(index));
    })
}

class Particle {
    constructor() {
        this.pos = createVector(random(width), random(height));
        this.vel = createVector(random(-2, 2), random(-2, 2));
        this.size = 10;
    }

    update() {
        this.pos.add(this.vel);
        this.edges();
    }

    draw() {
        noStroke();
        fill('rgba(255,255,255,0.5)');
        circle(this.pos.x, this.pos.y, this.size);
    }


    edges() {
        if(this.pos.x < 0 || this.pos.x > width) {
            this.vel.x *= -1;
        }
        if(this.pos.y < 0 || this.pos.y > height) {
            this.vel.y *= -1;
        }
    }

    checkParticles(particles) {
        particles.forEach(particle => {
            const d = dist(this.pos.x, this.pos.y, particle.pos.x, particle.pos.y)

            if(d < 120) {
                stroke('rgba(255,255,255,0.1)');
                line(this.pos.x, this.pos.y, particle.pos.x, particle.pos.y)
            }
        });
    }
}

//Magnifier Glass
var mainImg = document.getElementById("graph-image");
var preview = document.querySelector(".zoom-preview");

var x = preview.offsetWidth / 100;
var y = preview.offsetHeight / 100;

mainImg.addEventListener("mousemove", (e) => {
    preview.style.backgroundImage = `url(${mainImg.src})`;
    preview.style.backgroundSize = mainImg.width * x + 
      "px " + mainImg.height * y + "px";
    var posX = e.offsetX - 50;
    var posY = e.offsetY - 50;
    preview.style.backgroundPosition = "-" + posX * x + 
        "px -" + posY * y + "px";
});
mainImg.addEventListener("mouseout", () => {
    preview.style.backgroundImage = "none";
});


//Axes Callibration
let callibrateAxesActivated = false;
let axesCoords = []
function callibrateAxes(){
    callibrateAxesActivated = true;
};

function recordCoords(event) {
    const URL = '/get-coordinates'
    const xhr = new XMLHttpRequest();
    if(axesCoords.length < 4 && callibrateAxesActivated)
    {
        var x = event.clientX;
        var y = event.clientY;  
        tempCoord = [x, y]
        axesCoords.push(tempCoord)
        var coords = "X coords: " + x + ", Y coords: " + y;
        console.log(coords);
    };
    if(axesCoords.length == 4 && callibrateAxesActivated)
    {
        sender = JSON.stringify(axesCoords)
        xhr.open('POST', URL);
        xhr.send(sender);
        callibrateAxesActivated = false;
        openForm();
    };
    if(axesCoords.length == 4 && getPointValueActivated)
    {
        var x = event.clientX;
        var y = event.clientY;  
        tempCoord = [x, y]
        sender = JSON.stringify(tempCoord)
        xhr.open('POST', '/get_point');
        xhr.send(sender);
        getPointValueActivated = false;
        alert("complete");
    }
};

//Axes data form input function
function openForm() {
    document.getElementById("axes-form").style.display = "block";
};

function closeForm() {
    document.getElementById("axes-form").style.display = "none";
};

$(document).on('submit','#axes-form',function(e)
{
    console.log('hello');
    e.preventDefault();
    $.ajax({
        type:'POST',
        url:'/handle_data',
        data:{
        minX:$("#min-x").val(),
        maxX:$("#max-x").val(),
        minY:$("#min-y").val(),
        maxY:$("#max-y").val()
    },
    success:function()
    {
        alert('saved');
        closeForm();
    }
    })
});

//Get Point Value Function
let getPointValueActivated = false
function getPointValue()
{
    getPointValueActivated = true
    if (axesCoords.length != 4)
    {
        alert("Please callibrate axes first");
        getPointValueActivated = false;
    };
    
};

function getPos(e){
    let x=e.clientX;
    let y=e.clientY;
    let cursor="X: " + x + " Y: " + y;
    document.getElementById("display-area").innerHTML=cursor;
}

function stopTracking(){
    document.getElementById("display-area").innerHTML="";
}