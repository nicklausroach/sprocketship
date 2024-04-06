<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
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
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/nicklausroach/sprocketship" style="font-size: 60px; text-decoration: none;">
    ⚙️ 🚀
  </a>
<h3 align="center">Sprocketship</h3>

  <p align="center">
    Better stored procedure management
  </p>
</div>



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
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

`sprocketship` makes it easy to develop, manage, and deploy stored procedures in Snowflake. Using the language of your choosing, you can write the contents of your stored procedure separately from its configurations (e.g., `EXECUTE AS`, `RETURN TYPE`, etc.). 




### Built With

<a href=https://github.com/pipeline-tools/ABSQL>
<img src=https://raw.githubusercontent.com/pipeline-tools/ABSQL/598fcab4a5ccb1ca674c40e740b4edd9f99251a6/images/logo_400.svg width='150'>
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Installation

`pip install sprocketship`



<!-- USAGE EXAMPLES -->
## Usage

Currently, sprocketship expects a `.sprocketship.yml` file and a `procedures/` directory at the same level in a directory structure.

```
├── dbt_models
│   ├── customers.sql
│   ├── products.sql
├── procedures
│   ├── admin
│   │   ├── create_database_writer_role.js
│   │   ├── create_database_reader_role.js
│   ├── development
│   │   ├── create_temp_database.js
└── .sprocketship.yml
```

The yaml path to each procedure in the `sprocketship.yml` should follow that of the paths to their corresponding files in the `procedures/` directory. 

```
procedures:
  development:
    - name: create_temp_database
      database: !env_var SNOWFLAKE_DATABASE
      schema: !env_var SNOWFLAKE_SCHEMA
      ...

  admin:
    - name: create_database_reader
      database: !env_var SNOWFLAKE_DATABASE
      schema: !env_var SNOWFLAKE_SCHEMA
      ...

    - name: create_database_writer
      database: !env_var SNOWFLAKE_DATABASE
      schema: !env_var SNOWFLAKE_SCHEMA
      ...
```

From here, simply run 

`$ sprocketship liftoff` 

from the project directory (or provide the directory, e.g. `sprocketship liftoff my/directory/path`) and sprocketship will launch your stored procedures into the given directory. 

### Exhaustive Options for Stored Procedure Configuration

```
name: The name of the procedure
database: The name of the database where the procedure will be stored
schema: The name of the schema where the procedure will be stored
language: The language of the procedure definition
execute_as: caller or owner
args:
    - name: Name of argument
      type: Type of argument
      default: (Optional) default value for the argument
returns: The return type
comment: Explanation of the procedure
```

## Support

sprocketship currently only supports Javascript-based stored procedures (Python support coming soon!). Additionally, there are a few options from the `CREATE STORED PROCEDURE` function that are not yet supported:

* `RETURNS <result-data-type> NOT NULL`
* `CALLED ON NULL INPUT | { RETURNS NULL ON NULL INPUT | STRICT }`
* `VOLATILE | IMMUTABLE` (deprecated)


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/nicklausroach/sprocketship.svg?style=for-the-badge
[contributors-url]: https://github.com/nicklausroach/sprocketship/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/nicklausroach/sprocketship.svg?style=for-the-badge
[forks-url]: https://github.com/nicklausroach/sprocketship/network/members
[stars-shield]: https://img.shields.io/github/stars/nicklausroach/sprocketship.svg?style=for-the-badge
[stars-url]: https://github.com/nicklausroach/sprocketship/stargazers
[issues-shield]: https://img.shields.io/github/issues/nicklausroach/sprocketship.svg?style=for-the-badge
[issues-url]: https://github.com/nicklausroach/sprocketship/issues
[license-shield]: https://img.shields.io/github/license/nicklausroach/sprocketship.svg?style=for-the-badge
[license-url]: https://github.com/nicklausroach/sprocketship/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/nicklausroach
