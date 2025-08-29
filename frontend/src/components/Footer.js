import React from 'react';
import { Link } from 'react-router-dom';
import { Youtube, Music, Mail, MapPin } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-slate-900 border-t-2 border-red-600">
      <div className="container py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo & Description */}
          <div className="md:col-span-2">
            <div className="gazette-logo mb-4">
              <div className="gazette-logo-circle"></div>
              <div className="gazette-logo-text">
                The Crewkerne Gazette
              </div>
            </div>
            <p className="text-slate-400 mb-6 max-w-md">
              Unfiltered truth for the people. Bold journalism that challenges 
              the establishment and delivers the stories that matter most.
            </p>
            <div className="flex space-x-4">
              <a 
                href="https://m.youtube.com/@TheCrewkerneGazette" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-red-400 transition-colors"
              >
                <Youtube className="w-6 h-6" />
              </a>
              <a 
                href="https://open.spotify.com/artist/6iwYn8mBLB97HM21KSHsMa" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-red-400 transition-colors"
              >
                <Music className="w-6 h-6" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4 uppercase">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/news" className="text-slate-400 hover:text-red-400 transition-colors">
                  Breaking News
                </Link>
              </li>
              <li>
                <Link to="/music" className="text-slate-400 hover:text-red-400 transition-colors">
                  Latest Tracks
                </Link>
              </li>
              <li>
                <Link to="/documentaries" className="text-slate-400 hover:text-red-400 transition-colors">
                  Documentaries
                </Link>
              </li>
              <li>
                <Link to="/comedy" className="text-slate-400 hover:text-red-400 transition-colors">
                  Comedy & Satire
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-slate-400 hover:text-red-400 transition-colors">
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact & Admin */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4 uppercase">Contact</h3>
            <ul className="space-y-2">
              <li className="flex items-center text-slate-400">
                <MapPin className="w-4 h-4 mr-2" />
                Crewkerne, UK
              </li>
              <li className="flex items-center text-slate-400">
                <Mail className="w-4 h-4 mr-2" />
                CrewkerneGazette@gmail.com
              </li>
            </ul>
            
            {/* Admin Login - Hidden at bottom */}
            <div className="mt-6 pt-4 border-t border-slate-700">
              <Link 
                to="/login" 
                className="text-xs text-slate-600 hover:text-slate-400 transition-colors"
              >
                Staff Portal
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-slate-700 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-slate-400 text-sm">
            © 2024 The Crewkerne Gazette. All rights reserved.
          </p>
          <p className="text-slate-500 text-xs mt-2 md:mt-0">
            Truth. Integrity. Independence.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;