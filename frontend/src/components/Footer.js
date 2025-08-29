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
            <p className="text-red-300 font-semibold mb-3 text-lg">
              "Straight-talking news, culture, and comedy — proudly from Crewkerne."
            </p>
            <p className="text-slate-400 mb-6 max-w-md">
              Bold, unapologetic journalism with roots in Somerset and eyes on the nation. 
              Where common sense meets headlines.
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
            <h3 className="text-white font-bold text-lg mb-4 uppercase">Our Voice</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/news" className="text-slate-400 hover:text-red-400 transition-colors">
                  Sharp News
                </Link>
              </li>
              <li>
                <Link to="/music" className="text-slate-400 hover:text-red-400 transition-colors">
                  Authentic Music
                </Link>
              </li>
              <li>
                <Link to="/documentaries" className="text-slate-400 hover:text-red-400 transition-colors">
                  In-Depth Docs
                </Link>
              </li>
              <li>
                <Link to="/comedy" className="text-slate-400 hover:text-red-400 transition-colors">
                  Honest Comedy
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-slate-400 hover:text-red-400 transition-colors">
                  Have Your Say
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact & Admin */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4 uppercase">Get In Touch</h3>
            <ul className="space-y-2">
              <li className="flex items-center text-slate-400">
                <MapPin className="w-4 h-4 mr-2" />
                Somerset, England
              </li>
              <li className="flex items-center text-slate-400">
                <Mail className="w-4 h-4 mr-2" />
                CrewkerneGazette@gmail.com
              </li>
            </ul>
            
            <div className="mt-6">
              <p className="text-xs text-slate-500 mb-3">
                "News with bite. Culture with style. Comedy with grit."
              </p>
            </div>
            
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
        <div className="border-t border-slate-700 mt-8 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-slate-400 text-sm">
              © 2024 The Crewkerne Gazette. All rights reserved.
            </p>
            <div className="mt-2 md:mt-0 text-center md:text-right">
              <p className="text-red-400 text-sm font-semibold">
                "From Somerset to the nation — bold, unapologetic, alive."
              </p>
              <p className="text-slate-500 text-xs">
                No spin. No fluff. Just the Gazette.
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;