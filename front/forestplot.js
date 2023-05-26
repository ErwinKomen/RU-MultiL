function getCanvasXCoordinate(canvas, x, xRange) 
{
    var canvasWidth = canvas.width;
    var xRangeLength = xRange[1] - xRange[0];
    return canvasWidth * (x - xRange[0]) / xRangeLength;
}

function drawForestPlot(canvas, data, xRange) 
{
    const verticalOffset = 40;
    const verticalScale = 26;

    canvas.height = data.length * verticalScale + verticalOffset * 2;

    var canvasWidth = canvas.width;
    var xRangeLength = xRange[1] - xRange[0];
    var absoluteZeroPositionOnXAxis = getCanvasXCoordinate(canvas, 0, xRange);

    //Draw striped vertical zero line
    var ctx = canvas.getContext("2d");

    ctx.setLineDash([5, 3]);
    ctx.beginPath();
    ctx.moveTo(absoluteZeroPositionOnXAxis, 0);
    ctx.lineTo(absoluteZeroPositionOnXAxis, canvas.height);
    ctx.strokeStyle = "lightgray";
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.setLineDash([]);

    // X labels
    ctx.font = "12px Arial";

    // Display the text "Hello, world!" at coordinates (50, 50)
    for (var i = 0; i < xRangeLength; i++) 
    {
        var x = xRange[0] + i;
        var xCoordinate = getCanvasXCoordinate(canvas, x, xRange);
        ctx.fillText(i+xRange[0], xCoordinate, canvas.height - 10);
    }

    for (var i = 0; i < data.length; i++) 
    {
        var interval = data[i]["interval"];

        ctx.beginPath();
        ctx.moveTo(getCanvasXCoordinate(canvas, interval[0], xRange), verticalOffset + verticalScale * i);
        ctx.lineTo(getCanvasXCoordinate(canvas, interval[2], xRange), verticalOffset + verticalScale * i);
        ctx.strokeStyle = "lightgray";
        ctx.lineWidth = 2;
        ctx.stroke();		

        ctx.beginPath();
        ctx.arc(getCanvasXCoordinate(canvas, interval[1], xRange), verticalOffset + verticalScale * i, 5, 0, 2 * Math.PI);
        ctx.fillStyle = "black";
        ctx.fill();
    }
}
