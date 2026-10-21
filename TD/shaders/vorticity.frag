layout(location=0) out vec4 fragColor;
uniform vec4 uStep;
void main(){
    vec2 uv=vUV.st,t=uTD2DInfos[0].res.xy;
    float l=abs(texture(sTD2DInputs[1],uv-vec2(t.x,0)).x);
    float r=abs(texture(sTD2DInputs[1],uv+vec2(t.x,0)).x);
    float b=abs(texture(sTD2DInputs[1],uv-vec2(0,t.y)).x);
    float a=abs(texture(sTD2DInputs[1],uv+vec2(0,t.y)).x);
    vec2 gradient=vec2(r-l,a-b)*0.5;
    gradient/=length(gradient)+0.0001;
    float curl=texture(sTD2DInputs[1],uv).x;
    vec2 force=vec2(gradient.y,-gradient.x)*curl*uStep.w;
    vec2 velocity=texture(sTD2DInputs[0],uv).xy+force*uStep.x;
    fragColor=TDOutputSwizzle(vec4(velocity,0,1));
}
