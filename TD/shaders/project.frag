layout(location=0) out vec4 fragColor;
void main(){
    vec2 uv=vUV.st,t=uTD2DInfos[0].res.xy;
    float l=texture(sTD2DInputs[1],uv-vec2(t.x,0)).x;
    float r=texture(sTD2DInputs[1],uv+vec2(t.x,0)).x;
    float b=texture(sTD2DInputs[1],uv-vec2(0,t.y)).x;
    float a=texture(sTD2DInputs[1],uv+vec2(0,t.y)).x;
    vec2 velocity=texture(sTD2DInputs[0],uv).xy-0.5*vec2(r-l,a-b);
    if(uv.x<t.x || uv.x>1-t.x)velocity.x=0;
    if(uv.y<t.y || uv.y>1-t.y)velocity.y=0;
    fragColor=TDOutputSwizzle(vec4(velocity,0,1));
}
