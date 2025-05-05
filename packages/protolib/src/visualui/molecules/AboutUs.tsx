import { Element } from "@protocraft/core";

const AboutUs = (atoms) => {
    return <Element is={atoms.layout.Center} canvas height="90vh" width="100%" paddingHorizontal="20px">
        <Element is={atoms.layout.VStack} canvas height="100%" gap="20px" width="100%" maxWidth="900px" ai="center" jc="center">
            <Element is={atoms.basic.Image} canvas height={120} width={150} resizeMode='cover' url='/logo.png' ></Element>
            <Element is={atoms.text.Text} canvas fontFamily="$heading" fontSize="$12" fontWeight="700" >
                About Us
            </Element>
            <Element canvas is={atoms.text.Text} fontFamily="$body" fontSize="$6" textAlign="center" fontWeight="200" >
                Protofy is a Full-Stack, batteries included Low-Code enabled web/app and IoT system with an API system and real time messaging.
            </Element>
            <Element canvas is={atoms.miscellany.HCenterStack} gap="20px" marginTop="40px">
                <Element canvas is={atoms.miscellany.GithubIcon} height="35px" width="35px" />
                <Element canvas is={atoms.miscellany.DiscordIcon} height="35px" width="35px" />
                <Element canvas is={atoms.miscellany.TwitterIcon} height="35px" width="35px" />
            </Element>
        </Element >
    </Element>
}

AboutUs.craft = {
    custom: {
        light: "/images/molecules/aboutus-light.png",
        dark: "/images/molecules/aboutus-dark.png"
    },
    displayName: "AboutUs",
}

export default AboutUs;