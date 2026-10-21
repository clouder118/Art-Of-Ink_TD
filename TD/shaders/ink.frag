layout(location=0) out vec4 fragColor;
uniform vec4 uStep;
uniform float uReset;
uniform float uRestore;
// Mode, episode time, envelope, maintenance strength. In height-based units.
uniform vec4 uPalm;
vec2 palmVelocity(vec2 uv){
    const float aspect=1280.0/647.0;
    vec2 p=(uv-.5)*vec2(aspect,1.0);
    float r=length(p);
    vec2 radial=p/max(r,.00001);
    vec2 flow=vec2(0);
    float time=uPalm.y;
    if(uPalm.x<1.5){
        vec2 direction=normalize(vec2(aspect,1));
        vec2 across=vec2(-direction.y,direction.x);
        float span=length(vec2(aspect,1));
        float front=(fract(time/4.0)-.5)*(span+.5);
        float bend=dot(p,across)*8.0-time*1.7;
        float distance=dot(p,direction)-front-.07*sin(bend);
        float band=exp(-pow(distance/.10,2.0));
        flow=band*(.15*direction+.025*cos(bend)*across);
    }else if(uPalm.x<2.5){
        vec2 clockwise=vec2(radial.y,-radial.x);
        float arms=.65+.35*cos(3.0*atan(p.y,p.x+.000001)+8.0*r-time*1.2);
        float core=1.0-exp(-r*10.0);
        flow=(.12*clockwise+.04*radial)*core*arms*exp(-.8*r*r);
    }else{
        float radius=fract(time/3.0)*1.35;
        float band=exp(-pow((r-radius)/.075,2.0));
        float fade=smoothstep(0.0,.12,radius)*(1.0-smoothstep(1.12,1.35,radius));
        flow=.14*radial*band*fade;
    }
    float edge=smoothstep(0.0,.04,min(min(uv.x,1.0-uv.x),min(uv.y,1.0-uv.y)));
    return flow/vec2(aspect,1.0)*edge*uPalm.z*uPalm.w;
}
void main(){
    vec2 uv=vUV.st;
    vec2 velocity=texture(sTD2DInputs[1],uv).xy*uTD2DInfos[1].res.xy;
    // Add after projection, outside velocity feedback: bounded outward flow
    // survives the pressure solve without accumulating every rendered frame.
    if(uPalm.x>.5 && uPalm.z>.0001)velocity+=palmVelocity(uv);
    vec4 ink=texture(sTD2DInputs[0],clamp(uv-uStep.x*velocity,vec2(0),vec2(1)));
    vec4 original=texture(sTD2DInputs[2],uv);
    float restore=1.0-exp(-uRestore*uStep.x);
    vec4 color=mix(ink,original,restore);
    if(uReset>0.5)color=original;
    fragColor=TDOutputSwizzle(vec4(clamp(color.rgb,0.0,1.0),1));
}
