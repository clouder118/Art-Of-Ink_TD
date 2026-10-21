layout(location=0) out vec4 fragColor;
void main(){
    vec2 uv=vUV.st,t=uTD2DInfos[0].res.xy;
    float l=texture(sTD2DInputs[0],uv-vec2(t.x,0)).y;
    float r=texture(sTD2DInputs[0],uv+vec2(t.x,0)).y;
    float b=texture(sTD2DInputs[0],uv-vec2(0,t.y)).x;
    float a=texture(sTD2DInputs[0],uv+vec2(0,t.y)).x;
    fragColor=TDOutputSwizzle(vec4(0.5*(r-l-a+b),0,0,1));
}
