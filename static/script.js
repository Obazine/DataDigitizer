

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
//A copy of the image is created, it is then enlarged and an offset value is calculated so that the centre is the same as cursor pointer
var mainImg = document.getElementById("graph-image");
var preview = document.querySelector(".zoom-preview");
var x = preview.offsetWidth / 50;
var y = preview.offsetHeight / 50;
mainImg.addEventListener("mousemove", (e) => {
    preview.style.backgroundImage = `url(${mainImg.src})`;
    preview.style.backgroundSize = mainImg.width * x + 
      "px " + mainImg.height * y + "px";
    var posX = e.offsetX - 25;
    var posY = e.offsetY - 25;
    preview.style.backgroundPosition = "-" + posX * x + 
        "px -" + posY * y + "px";
});
mainImg.addEventListener("mouseout", () => {
    preview.style.backgroundImage = "none";
});

//Axes Callibration
//axesCoords list is used to temporarily store the coordinates for the axes
//The axesCoords list is cleared everytime the function is called
//The recordCoords function is used to also mark the points where the user wants to get the value. 
//The data is sent through their respective routes and data is added to the database
let callibrateAxesActivated = false;
let axesCoords = []
function callibrateAxes(){
    callibrateAxesActivated = true;
    axesCoords=[];
};
function recordCoords(event) {
    const URL = '/axes_calibration'
    const xhr = new XMLHttpRequest();
    if(axesCoords.length < 4 && callibrateAxesActivated)
    {
        let rect = event.target.getBoundingClientRect();
        let x = Math.round(event.clientX - rect.left);
        let y = Math.round(event.clientY - rect.top); 
        console.log(x, y) 
        var tempCoord = [x, y]
        axesCoords.push(tempCoord)
        var coords = "X coords: " + x + ", Y coords: " + y;
        console.log(coords);  
        $("body").append(            
            $('<div class="marker"></div>').css({       
                position: 'absolute',
                top: event.pageY-3 + 'px',
                left: event.pageX-3 + 'px',
                width: '6px',
                height: '6px',
                background: '#ff0000'
            })              
        );
    };
    if(axesCoords.length == 4 && callibrateAxesActivated)
    {
        $(".marker").remove();
        sender = JSON.stringify(axesCoords)
        xhr.open('POST', URL);
        xhr.send(sender);
        callibrateAxesActivated = false;
        openAxesForm();
    };
    if((axesCoords.length == 4 || axescallibrated)&& getPointValueActivated)
    {
        $("body").append(            
            $('<div class="marker"></div>').css({      
                position: 'absolute',
                top: event.pageY-3 + 'px',
                left: event.pageX-3 + 'px',
                width: '6px',
                height: '6px',
                background: '#000000'
            })              
        );
        let rect = event.target.getBoundingClientRect();
        let x = Math.round(event.clientX - rect.left);
        let y = Math.round(event.clientY - rect.top);
        tempCoord = [x, y]
        sender = JSON.stringify(tempCoord)
        xhr.open('POST', '/get_point');
        xhr.send(sender);
    }
};

//Axes data form input function
//Displays and hides the axes form pop up. Sends the data to the route within the Flask application using ajax
function openAxesForm() {
    document.getElementById("axes-form").style.display = "block";
};
function closeAxesForm() {
    document.getElementById("axes-form").style.display = "none";
};
$(document).on('submit','#axes-form',function(e)
{
    e.preventDefault();
    $.ajax({
        type:'POST',
        url:'/data_calibration',
        data:{
        minX:$("#min-x").val(),
        maxX:$("#max-x").val(),
        minY:$("#min-y").val(),
        maxY:$("#max-y").val()
    },
    success:function()
    {
        alert('saved');
        closeAxesForm();
    }
    })
});

//Dataset creation form
//Same as axes pop up form, just the values are different
function openCreateDatasetForm() {
    if(!document.getElementById("username"))
    {
        alert("Please log in or sign in first");
    }
    else 
    {
        document.getElementById("dataset-creation-form").style.display = "block";
    };
};
function closeCreateDatasetForm() {
    document.getElementById("dataset-creation-form").style.display = "none";
};
$(document).on('submit','#dataset-creation-form',function(e)
{
    e.preventDefault();
    $.ajax({
        type:'POST',
        url:'/create_dataset',
        data:{
        datasetName:$("#dataset-name").val(),
    },
    success:function()
    {
        alert('saved');
        closeCreateDatasetForm();
        window.location.replace(window.location.href);
    }
    })
});

//Dataset Selection form
function openSelectDatasetForm() {
    if(!document.getElementById("username"))
    {
        alert("Please log in or sign in first");
    }
    else 
    {
        document.getElementById("dataset-selection-form").style.display = "block";
    };
};
function closeSelectDatasetForm() {
    document.getElementById("dataset-selection-form").style.display = "none";
};


//Dataset Delection form
function openDeleteDatasetForm() {
    if(!document.getElementById("username"))
    {
        alert("Please log in or sign in first");
    }
    else 
    {
        document.getElementById("dataset-delection-form").style.display = "block";
    };
};
function closeDeleteDatasetForm() {
    document.getElementById("dataset-delection-form").style.display = "none";
};

//Axes Label form
function openAxesLabelForm() {
    document.getElementById("axes-label-form").style.display = "block";
};
function closeAxesLabelForm() {
    document.getElementById("axes-label-form").style.display = "none";
};

//Auto Extract form
function openAutoExtractForm() {
    document.getElementById("auto-extract-form").style.display = "block";
};
function closeAutoExtractForm() {
    document.getElementById("auto-extract-form").style.display = "none";
};


//Get Point Value Function
//Checks if axes have been calibrated first, then sets a bool variable to true, activating the get point function everytime mouse clicks on image
let getPointValueActivated = false
function getPointValue()
{
    getPointValueActivated = true
    if (axescallibrated)
    {
    }
    else if (axesCoords.length != 4)
    {
        alert("Please callibrate axes first");
        getPointValueActivated = false;
    };
    
};

function getAutoValue()
{
    if (axescallibrated)
    {
    }
    else if (axesCoords.length != 4)
    {
        alert("Please callibrate axes first");
    };
    
};

//Mouse Coordinates display
//Gets relative mouse coordinate within the image container
function getPos(e){
    let rect = e.target.getBoundingClientRect();
    let x = Math.round(e.clientX - rect.left);
    let y = Math.round(e.clientY - rect.top);
    let cursor="X: " + x + " Y: " + y;
    document.getElementById("display-coord").innerHTML=cursor;
}

function stopTracking(){
    document.getElementById("display-coord").innerHTML="";
}

//Auto Extract slider
var slider = document.getElementById("threshold");
var output = document.getElementById("threshpreview");
output.innerHTML = slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
slider.oninput = function() {
    output.innerHTML = this.value;
}