layout(location=0) out vec4 fragColor;
void main(){
    vec2 uv=vUV.st,t=uTD2DInfos[0].res.xy;
    vec2 c=texture(sTD2DInputs[0],uv).xy;
    float l=texture(sTD2DInputs[0],uv-vec2(t.x,0)).x;
    float r=texture(sTD2DInputs[0],uv+vec2(t.x,0)).x;
    float b=texture(sTD2DInputs[0],uv-vec2(0,t.y)).y;
    float a=texture(sTD2DInputs[0],uv+vec2(0,t.y)).y;
    if(uv.x<t.x)l=-c.x;if(uv.x>1-t.x)r=-c.x;
    if(uv.y<t.y)b=-c.y;if(uv.y>1-t.y)a=-c.y;
    fragColor=TDOutputSwizzle(vec4(0.5*(r-l+a-b),0,0,1));
}
