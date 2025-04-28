<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[//]: # ([![Contributors][contributors-shield]][contributors-url])

[//]: # ([![Forks][forks-shield]][forks-url])

[//]: # ([![Stargazers][stars-shield]][stars-url])

[//]: # ([![Issues][issues-shield]][issues-url])

[//]: # ([![LinkedIn][linkedin-shield]][linkedin-url])

# Lecture slide sync

<!-- PROJECT LOGO -->

<img alt="Thumbnail" height="400" src="images/Thumbnail_final.svg" width="400" style="display:block; margin: 0 auto"/>

<br>

[//]: # (<div align="center">)

[//]: # (<!--)

[//]: # (  <a href="https://github.com/DanValnicek/slide-lecture-sync">)

[//]: # (    <img src="images/Thumbnail_final.svg" alt="Logo" width="80" height="80"> )

[//]: # (  </a>)

[//]: # (-->)

[//]: # ()

[//]: # ()
[//]: # (  <p align="center">)

[//]: # (    A PDF viewer and video player capable of skipping lecture video by slide.)

[//]: # (    Lecture Slide Sync has a functionality enabling automatic slide to frame synchronization.)

[//]: # ()
[//]: # (    <br />)

[//]: # (    <a href="https://github.com/DanValnicek/slide-lecture-sync"><strong>Explore the docs »</strong></a>)

[//]: # (    <br />)

[//]: # (    <br />)

[//]: # (    <a href="https://github.com/DanValnicek/slide-lecture-sync">View Demo</a>)

[//]: # (    &middot;)

[//]: # (    <a href="https://github.com/DanValnicek/slide-lecture-sync/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>)

[//]: # (    &middot;)

[//]: # (    <a href="https://github.com/DanValnicek/slide-lecture-sync/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>)

[//]: # ()
[//]: # (  </p>)

[//]: # (</div>)



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->

## About The Project

[//]: # (<iframe width="560" height="315")

[//]: # (src="https://youtu.be/Ui0M3u0Rpxk")

[//]: # (frameborder="0")

[//]: # (allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture")

[//]: # (allowfullscreen></iframe>)

<div align="center">
  <a href="https://www.youtube.com/watch?v=Ui0M3u0Rpxk"><img src="https://img.youtube.com/vi/Ui0M3u0Rpxk/0.jpg" alt="Youtube video showcase"></a>
</div>

[//]: # ([![Video showcase]&#40;http://img.youtube.com/vi/Ui0M3u0Rpxk/0.jpg&#41;]&#40;https://youtu.be/Ui0M3u0Rpxk&#41; )

This app was made to make the search for a specific part of lecture easier, by creating a list of time intervals for each slide in a supplied PDF presentation.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

[![Python][python-shield]][python-url]


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->

## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Installation

You can download already precompiled .exe from releases.

> Currently running on linux doesn't work due to issues with the shiboken6 library.
 
Another option is to clone it and run it yourself using conda: 
1. Clone the repo
   ```sh
   git clone https://github.com/DanValnicek/slide-lecture-sync.git
   ```
2. Install conda by following instructions at [anaconda.com](https://www.anaconda.com/docs/getting-started/miniconda/install#windows-power-shell)
3. Enter `./env` and create and activate environment
    ```sh
        cd ./env
        conda env create -f environment.yml
        conda activate slide-lecture-sync
    ```
4. Update the environment
    ```sh
   conda env update -n slide-lecture-sync --prune
   ```
5. Move to project root and run main.py
    ```sh
   cd ..
   python main.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->

## Usage

The core of the application is a PDF viewer that can be used normally.
In case 
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->

## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](https://github.com/DanValnicek/slide-lecture-sync/issues) for a full list of proposed features (and known
issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any
contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also
simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>
 
<!-- LICENSE -->

## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->

## Contact

Dan Valníček 

Project Link: [https://github.com/DanValnicek/slide-video-sync](https://github.com/DanValnicek/slide-video-sync)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License
[![project_license][license-shield]][license-url]


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[python-shield]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[python-url]: https://www.python.org/

[stars-shield]: https://img.shields.io/github/stars/DanValnicek/slide-lecture-sync.svg?style=for-the-badge

[stars-url]: https://github.com/DanValnicek/slide-lecture-sync/stargazers

[issues-shield]: https://img.shields.io/github/issues/DanValnicek/slide-lecture-sync.svg?style=for-the-badge

[issues-url]: https://github.com/DanValnicek/slide-lecture-sync/issues

[license-shield]: https://img.shields.io/github/license/DanValnicek/slide-lecture-sync.svg?style=for-the-badge

[license-url]: https://github.com/DanValnicek/slide-lecture-sync/blob/master/LICENSE.txt

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555

[linkedin-url]: https://linkedin.com/in/linkedin_username

[product-screenshot]: images/screenshot.png

[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white

[Next-url]: https://nextjs.org/

[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB

[React-url]: https://reactjs.org/

[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D

[Vue-url]: https://vuejs.org/

[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white

[Angular-url]: https://angular.io/

[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00

[Svelte-url]: https://svelte.dev/

[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white

[Laravel-url]: https://laravel.com

[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white

[Bootstrap-url]: https://getbootstrap.com

[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white

[JQuery-url]: https://jquery.com 