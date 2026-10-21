layout(location=0) out vec4 fragColor;
uniform vec4 uStep;
uniform float uReset;
uniform float uRestore;
void main(){
    vec2 uv=vUV.st;
    vec2 velocity=texture(sTD2DInputs[1],uv).xy*uTD2DInfos[1].res.xy;
    vec4 ink=texture(sTD2DInputs[0],clamp(uv-uStep.x*velocity,vec2(0),vec2(1)));
    vec4 original=texture(sTD2DInputs[2],uv);
    float restore=1.0-exp(-uRestore*uStep.x);
    vec4 color=mix(ink,original,restore);
    if(uReset>0.5)color=original;
    fragColor=TDOutputSwizzle(vec4(clamp(color.rgb,0.0,1.0),1));
}
